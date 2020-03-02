find . -name "*.py" -or -name "*.json" -exec sed --in-place=".bak" -e 's/[ 	]*$//g' {} \;
