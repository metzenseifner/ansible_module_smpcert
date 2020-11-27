FROM centos:7

MAINTAINER "Jonathan L. Komar" <komar.jonathan@gmail.com>

ENV container docker

# see https://github.com/docker-library/docs/tree/master/centos#systemd-integration
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done);\
  rm -f /lib/systemd/system/multi-user.target.wants/*;\
  rm -f /etc/systemd/system/*.wants/*;\
  rm -f /lib/systemd/system/local-fs.target.wants/*; \
  rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
  rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
  rm -f /lib/systemd/system/basic.target.wants/*;\
  rm -f /lib/systemd/system/anaconda.target.wants/*;

ADD ./start.sh /start.sh
ADD ./run.sh /run.sh
Add ./cacert.pem /root/cacert.pem

RUN yum -y update;\
    yum -y install openssh-server openssh-clients passwd sudo vim;\
    yum clean all;\
    ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N '';\
    #sed -Ei.orig 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config && sed -ri 's/#UsePAM no/UsePAM no/g' /etc/ssh/sshd_config;\
    sed -Ei.orig 's|(/usr/libexec/openssh/sftp-server$)|\1 -l VERBOSE|' /etc/ssh/sshd_config;\
    sed -Ei.orig '/^Subsystem[ \t]+sftp.*/a Match LocalPort 22022\nAllowTCPForwarding no\nForceCommand internal-sftp' /etc/ssh/sshd_config;\
    systemctl enable sshd;\
    mkdir /var/run/sshd;\
    install -d -m 777 /certs;\
    chmod 755 /start.sh /run.sh;\
    ./start.sh

# VERBOSE sftp logs in /var/log/messages

VOLUME [ "/sys/fs/cgroup" ]
ENV AUTHORIZED_KEYS nil
ENV CERT nil

EXPOSE 22

CMD ["/run.sh"]
