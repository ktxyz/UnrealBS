echo "I'm a long thread"

for i in {1..10000000} ; do
  echo $i
done

echo "I finished"
exit 0