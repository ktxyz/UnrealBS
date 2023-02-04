echo "I'm a long thread"

for i in {1..100000} ; do
  echo $i
done

echo "I finished"
exit 0