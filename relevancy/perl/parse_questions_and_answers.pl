use strict;

my (%hash, $text, $BLOCK);
while(<>){
  next unless /\S/;

  if (/ - Is (\d+).pdf relevant to the question:/) {

    my $_key = remove_logstamps($_); 
    $hash{$_key} = $hash{$_key} + 1;
    next if $hash{$_key} > 1;

    $text = $text . remove_logstamps($_);
    $BLOCK=1;
  
    while (<>) {
      while($BLOCK != 0) {
        $text = $text . remove_logstamps($_);
        if (/ - Answer: /) {
          $BLOCK = 0;
        }
      }
      last;
    }
    if ($hash{$text} < 2) {
	    print $text;
    }
  }
  $text = "\n";
}

sub remove_logstamps {
  my $_tmp = $_[0];
  # 2025-01-05 02:47:24,619 - INFO - 
  $_tmp =~ s/\d+-\d+-\d+\s+\d+:\d+:\d+,\d+ - INFO - //;
  return $_tmp;
}
