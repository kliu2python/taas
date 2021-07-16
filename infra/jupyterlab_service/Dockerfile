FROM python:3.6.12-slim-buster

COPY . /root/.jupyter/

RUN pip3 install jupyterlab

WORKDIR /shared_folder

#RUN echo y | jupyter kernelspec remove python3
RUN pip3 uninstall -y  ipykernel
CMD ["sh", "/root/.jupyter/start_jupyter_lab.sh"]
