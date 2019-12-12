SECTIONS {
    . = 0x00000000;
    .reset 0x00 : { * (.reset); }
    .exceptions 0x20 : { * (.exceptions); }
    .text : { * (.text); }
    .data : { * (.data); }
}
