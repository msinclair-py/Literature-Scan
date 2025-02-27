model="meta-llama/Meta-Llama-3.1-70B-Instruct"
import getpass
import os

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, StateGraph, START

def create_agent(llm, tools, system_message: str):
    """Create an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)


## Define the tools ##
from langchain_core.tools import tool

@tool
def get_pmcids(term):
    ''' Use this to search pubmed central for research papers associated with term.'''

    url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
    url = url + f'db=pmc&term={term}[Title/Abstract]+AND+free+fulltext%5bfilter%5d&retmode=json'
    response = requests.get(url, )

    if response.status_code == 200:
        json_response = response.json()
        arr = json_response['esearchresult']['idlist']

    else:
        print(f"Error: {response.status_code} - {response.text}")
        arr = []

    return arr

from typing import Annotated

@tool
def python_repl(code: Annotated[str, "The python code to execute to search pubmed central"]):
    '''Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user.'''

    try:
        result = repl.run(code)
    except BaseException as e:
        return f'Failed to execute. Error: {repr(e)}'
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return (result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER.")


## Define State ##
import operator
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI

# This defines the object that is passed between each node
# in the graph. We will create different nodes for each agent and tool
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str

## Define Agent Nodes ##
import functools
from langchain_core.messages import AIMessage

# Helper function to create a node for a given agent
def agent_node(state, agent, name):
    result = agent.invoke(state)
    # We convert the agent output into a format that is suitable to append to the global state
    if isinstance(result, ToolMessage):
        pass
    else:
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
    return {
        "messages": [result],
        # Since we have a strict workflow, we can
        # track the sender so we know who to pass to next.
        "sender": name,
    }

key = 'acmsc-35360'
openai_api_base = 'http://rbdgx2.cels.anl.gov:9999/v1'
llm = ChatOpenAI(
            api_key=key,
            base_url=openai_api_base,
        )

# Research agent and node
get_pcmids_tool = get_pcmids
research_agent = create_agent(
    llm,
    [get_pmcids_tool],
    system_message="You should provide accurate data for the chart_generator to use.",
)

