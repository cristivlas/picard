find . -name "*.py" -or -name "*.json" -exec sed --in-place=".bak" 's/[[:blank:]]*$//g' {} \;
