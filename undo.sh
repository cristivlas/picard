find . -name *.json.bak | while read f
do
	g=`echo $f | sed -e 's/\.bak//g'`
	echo $f "-->" $g
	mv $f $g

done
