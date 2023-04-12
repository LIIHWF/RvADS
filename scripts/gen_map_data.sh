WORKSPACE=$(bazel info workspace)
MAP_DIR=$WORKSPACE/data/map/$1
if [ ! -d $MAP_DIR ]; then
  mkdir -p $MAP_DIR
fi
bazel run //adsv/tools/apollo_map_handler $1 $WORKSPACE
