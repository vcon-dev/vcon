#!/bin/bash

# configuration

IMAGE_NAME="vcon_core_pydev3_8"
CONTAINER_NAME="${IMAGE_NAME}_container"
CONTAINER_HOSTNAME="${IMAGE_NAME}_${HOSTNAME}"

# Intensionally exclude: root
SHORT_CUT_NAMES="build resume run shell stop remove"
ALL_COMMANDS="${SHORT_CUT_NAMES} root"

confirm()
{
  operation=$1
  echo "Are you sure that you want to ${operation} (y/N)?" 1>&2
  read answer
  answer=`echo -n "${answer}" | awk '{print tolower($0)}'`
  case ${answer} in
    y)
      result="True"
      ;;

    yes)
      result="True"
      ;;

    *)
      result="False"
      ;;

  esac

  echo -n "${result}"
}

check_build()
{
  IMAGE_ID=`docker images -q ${IMAGE_NAME}`
  if [ -z "${IMAGE_ID}" ]
  then
    echo "Image: ${IMAGE_NAME} not built"
    do_build
  else
    echo "Image: ${IMAGE_NAME} previously built"
  fi
}

container_status()
{
  PS_LINE=`docker ps -f name=${1} | tail -n +2`
  if [ -z "${PS_LINE}" ]
  then
    PS_LINE=`docker ps -f status=exited -f name=${1} | tail -n +2`
    if [ -z "${PS_LINE}" ]
    then
      STATUS="none"
    else
      STATUS="exited"
    fi

  else
    STATUS="running"
  fi

  echo -n "${STATUS}"
}

make_short_cut_links()
{
  dir_name=$1
  script_name=$2
  script_path=${dir_name}/${script_name}

  if [ -z "${script_name}" ]
  then
    echo "ERROR: incorrect script name is empty string"
    exit 1
  elif [ ! -e "${script_path}" ]
  then
    echo "ERROR: incorrect script dir or name, ${script_path} does not exist"
    exit 1
  elif [ ! -x "${script_path}" ]
  then
    echo "ERROR: script ${script_path}  is not executable"
    exit 1
  fi

  for short_cut in $SHORT_CUT_NAMES
  do
    short_cut_path="${dir_name}/${short_cut}"
    if [ -L "${short_cut_path}" ]
    then
      #echo "${short_cut_path} is a link"
      true
    elif [ -e "${short_cut_path}" ]
    then
      #echo "${short_cut_path} is not a link"
      true
    else
      #echo "creating ${short_cut_path} link"
      ln -s ${script_path} ${short_cut_path}
    fi
  done
}

#echo "UID: ${UID}"

make_short_cut_links `dirname $0` `basename $0`

if [ $0 == "./dockerctl.sh" ]
then
  if [ $# -ge 1 ]
  then
    COMMAND=$1
    shift
  else
    echo "No command provided"
    exit 1
  fi
else
  COMMAND=`basename $0`
fi

echo "command: ${COMMAND}"

do_build()
{
  # Set UID same as host machine so that file owner does not get screwed up
  # in the shared directory
  BUILD_COMMAND="docker build --build-arg user=${USER} --build-arg UID=${UID} -t ${IMAGE_NAME} ."
  echo ${BUILD_COMMAND}
  ${BUILD_COMMAND}
}

do_run()
{
  check_build

  CONTAINER_STATUS=`container_status ${CONTAINER_NAME}`

  case ${CONTAINER_STATUS} in
    running)
      echo "container ${CONTAINER_NAME} already running"
      echo "shell, stop or kill and run again"
      exit 5
      ;;

    exited)
      echo "container ${CONTAINER_NAME} has previously exited"
      echo "resume or remove and run again"
      exit 5
      ;;

    none)
      echo "container ${CONTAINER_NAME} does not exist"
      # port mapping -p from:to
      # -p 9000:8080
      # volume mounting -v
      docker run -it \
        -h ${CONTAINER_HOSTNAME} \
        --name="${CONTAINER_NAME}" \
        --volume="/home/${USER}:/home/${USER}" \
        --net host \
        ${IMAGE_NAME}
      ;;

    *)
      echo "container ${CONTAINER_NAME} unknown status:  ${CONTAINER_STATUS}"
      exit 7
      ;;
  esac

}

do_stop()
{
  CONTAINER_STATUS=`container_status ${CONTAINER_NAME}`
  if [ "${CONTAINER_STATUS}" != "running" ]
  then
    echo "container ${CONTAINER_NAME} is not running."
    exit 9 
  fi 
  docker stop -t 10 ${CONTAINER_NAME}
}

do_remove()
{
  CONTAINER_STATUS=`container_status ${CONTAINER_NAME}`
  if [ "${CONTAINER_STATUS}" == "running" ]
  then
    echo "container ${CONTAINER_NAME} is running."
    echo "You have to stop or kill the container before removing."
    exit 8
  fi 
  docker container rm ${CONTAINER_NAME}
}

do_resume()
{
  docker start -a -i ${CONTAINER_NAME}
}


do_shell()
{
  check_build

  CONTAINER_STATUS=`container_status ${CONTAINER_NAME}`

  case ${CONTAINER_STATUS} in
    running)
      echo "argc: $# arg[1]: $1"
      if [ $# -eq 1 -a "$1" == "root" ]
      then
        echo "starting root shell"
        docker exec -it -u root ${CONTAINER_NAME} /bin/bash
      else
        echo "starting shell"
        docker exec -it ${CONTAINER_NAME} /bin/bash
      fi
      ;;

    exited)
      echo "container ${CONTAINER_NAME} has previously exited"
      echo "resume or kill and run again"
      exit 5
      ;;

    none)
      echo "container ${CONTAINER_NAME} does not exist"
      echo "run first"
      exit 6
      ;;

    *)
      echo "container ${CONTAINER_NAME} unknown status:  ${CONTAINER_STATUS}"
      exit 7
      ;;
  esac
}

do_help()
{
  echo "available commands:"
  echo " ${ALL_COMMANDS}"
}

do_done_help()
{
  echo "You many have wanted one of the following commands:"
  echo "	To stop the CMD process in the container with a graceful shutdown time of 10 seconds:"
  echo "		docker stop -t 10 ${CONTAINER_NAME}"
  echo "	To kill the container with no graceful shutdown:"
  echo "		docker kill ${CONTAINER_NAME}"
  echo "	To remove the container to do a clean run or new build:"
  echo "		docker container rm ${CONTAINER_NAME}"
  exit 3 
}

case ${COMMAND} in
  build)
    do_build
    ;;

  help)
    do_help
    ;;

  resume)
    do_resume
    ;;

  root)
    do_shell root
    ;;

  run)
    do_run
    ;;

  shell)
    do_shell
    ;;

  kill)
    do_done_help
    ;;
  stop)
    if [ "True" == `confirm "stop running the container ${CONTAINER_NAME}"` ]
    then
      do_stop
    else
      do_done_help
    fi
    ;;
  remove)
    if [ "True" == `confirm "remove the container ${CONTAINER_NAME}"` ]
    then
      do_remove
    else
      do_done_help
    fi
    ;;
  delete)
    do_done_help
    ;;
  "done")
    do_done_help
    ;;
  *)
    echo "Command: ${COMMAND} not defined"
    do_help
    exit 2
esac



