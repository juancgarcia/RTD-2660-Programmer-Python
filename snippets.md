
### Hex view
```sh
$ i=../flash-test.bin; cat $i | od -t x1 > "$i.hex_str"
```
> Translates binary files to a text format like this:
```sh
0000000 02 10 cf 09 0a 0b 0c 0d 10 04 04 02 11 ef ff ff
0000020 ff ff ff 02 12 fb ec 4d 60 11 e8 49 70 17 ed 33
0000040 ec 33 04 60 0d e4 fc ff fe fd 22 e9 33 e8 33 04
...
```
> I don't have a binary diff tool, so this was very helpful for attempting to diff or match firmware dumps to corresponding .bins from my RTD2660 firmware archive. (I got mine from this [forum post](http://forum.banggood.com/forum-topic-67095.html) on [BangGood](http://www.banggood.com/).)
> Particularly since my tool might leave some extraneous cruft at the end of the dump, you can get a pretty good idea how closely the dump compares to an existing bin by visually comparing it in a standard diff program. Especially afternarrowing it down with...


```sh
len=16
for i in $(find ../firmware/ -type f -iname "*.bin" -print | sort); do
    str=$(od --width=$len --read-bytes=$len -t x1 $i | cut -c 8-);
    echo $str $i;
done > ${len}head_firmwares.txt
```
> Creates a listing of all your firmware files like the following, which made it easy to quickly narrow down matching firmware candidates to my dumped image.
```sh
02 10 78 09 0a 0b 0c 0d 10 04 04 02 11 98 ff ff ./firmware/LOGO/1366x768-6bit-致力科技LOGO.BIN
02 10 7e 09 0a 0b 0c 0d 10 04 04 02 11 9e ff ff ./firmware/LOGO/PCB800099-LVDS1280X800-D6BIT-2AV1VGA1HDMI-ACC-IR2-5KEY-NJ6800-LOGO-5S.bin
02 10 7e 09 0a 0b 0c 0d 10 04 04 02 11 9e ff ff ./firmware/LOGO/PCB800099-LVDS1280X800-D6BIT-2AV1VGA1HDMI-ACC-IR2-5KEY-NJ6800-黑底红字LOGO-5S.bin
02 0f 52 09 0a 0b 0c 0d 10 04 04 02 10 72 00 00 ./firmware/PCB800099++PCB800100-TTL-480X272-AT043TN24V.1-2AV1VGA-1HDMI-5KEY-IR2-带倒车--无信号20S侍机-20121023.BIN
...
```
> 16 bytes seemed to work well enough for my purposes, but feel free to play with that.
