FROM python:2.7

COPY . /opt/hts

WORKDIR /opt/hts

# force install requirements
# make -B is also an option
RUN rm .deps && make deps

EXPOSE 5000
CMD ["bash", "./run.sh"]
