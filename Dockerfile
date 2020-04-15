FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

RUN apt-get update
ENV PYTHONUNBUFFERED=True

RUN apt-get install --yes vim

WORKDIR /opt

RUN curl --location https://sourceforge.net/projects/rdp-classifier/files/latest/download > rdp_classifier.zip && \
unzip rdp_classifier.zip && \
rm rdp_classifier.zip

RUN pip install pandas dotmap

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
