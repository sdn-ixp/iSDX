for i in specs/*.spec
do
	echo "####################################" $i "########################################################"
	file=`basename $i .spec`
	rm -rf ../examples/$file
	rm -rf output/$file
	python gen_test.py $i
	mv output/$file ../examples
done