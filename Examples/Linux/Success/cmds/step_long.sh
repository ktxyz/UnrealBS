echo "I'm a long thread"

for i in {1..1500} ; do
  echo $i
done

echo "I finished"
exit 0