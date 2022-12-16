# Ubuntu 20.4
#FROM ubuntu:focal
FROM 11.8.0-cudnn8-runtime-ubuntu20.04
#FROM scratch
#ADD ubuntu-focal-oci-amd64-root.tar.gz /

# apt stuff
RUN mkdir /root/install
COPY apt_package_list.txt /root/install/
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3.8
RUN apt-get install -y $(grep -vE "^\s*#" /root/install/apt_package_list.txt | tr "\n" " ")

# pip stuff
RUN /usr/bin/python3.8 -m pip install --upgrade pip
RUN pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U
COPY pip_package_list.txt /root/install
RUN  pip3 install -r /root/install/pip_package_list.txt

# User setup
ARG UID=1001
ARG USER=dpetrie
RUN adduser --uid ${UID} ${USER}
USER ${USER}
#RUN mkdir /home/${USER}
#RUN chown ${UID}.${UID} /home/${USER}

CMD ["bash"]


