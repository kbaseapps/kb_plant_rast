FROM kbase/kbase:sdkbase2.latest
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update

# Here we install a python coverage tool and an
# https library that is out of date in the base image.

RUN pip install coverage

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN curl -s https://raw.githubusercontent.com/ModelSEED/PlantSEED/master/Data/PlantSEED_v2/Flat_Files/Supporting_Data_S3_Signature_Kmers.txt > /kb/module/data/functions_kmers.txt

WORKDIR /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
