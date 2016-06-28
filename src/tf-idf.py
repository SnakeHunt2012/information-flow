#!/usr/bin/env python
# -*- coding: utf-8

from re import compile
from json import dumps
from codecs import open
from numpy import log
from jieba import cut
from argparse import ArgumentParser
from progressbar import ProgressBar

def main():

    parser = ArgumentParser()
    parser.add_argument("url_file", help = "url_file")
    parser.add_argument("content_file", help = "content_file")
    parser.add_argument("data_file", help = "data_file")
    parser.add_argument("template_file", help = "template_file")
    args = parser.parse_args()
    
    url_file = args.url_file
    content_file = args.content_file
    data_file = args.data_file
    template_file = args.template_file

    url_re = compile("(?<=<url:)[^>]*(?=>)")
    content_re = compile("(?<=<content:)[^>]*(?=>)")
    image_sub = compile("\[img\][^\[\]]+\[/img\]")
    br_sub = compile("\[br\]")

    tag_dict = {"0": 0, "1":1, "2":1, "3":0, "4":1, "5":1}

    # url_dict
    print "aggregating url dict (url -> label) ..."
    url_dict = {} # url -> label
    with open(url_file, 'r') as fd:
        for line in fd:
            splited_line = line.strip().split("\t")
            if len(splited_line) != 4:
                continue
            url, email, tag, timestamp = splited_line
            if url not in url_dict:
                url_dict[url] = tag_dict[tag]
    print "aggregating url dict (url -> label) done."

    # doc_list
    print "aggregating doc list [(url, seg_list)] ..."
    doc_list = [] # [(url, seg_list), (url, seg_list), ...]
    with open(content_file, 'r') as fd:
        progress = ProgressBar(maxval = len(url_dict)).start()
        counter = 0
        for line in fd:
            if not line.startswith("<flag:0>"):
                continue
            line = line.strip()
            
            result = url_re.search(line)
            if not result:
                continue
            url = result.group(0)

            result = content_re.search(line)
            if not result:
                continue
            content = result.group(0)

            content = image_sub.sub("", content)
            content = br_sub.sub("\n", content)
            seg_list = [seg.encode("utf-8") for seg in cut(content)]

            doc_list.append((url, seg_list))
            
            counter += 1
            progress.update(counter)
        progress.finish()
    print "aggregating doc list [(url, seg_list)] done"

    # df_dict
    print "aggregating df dict (word -> df) ..."
    df_dict = {}
    
    progress = ProgressBar(maxval = len(doc_list)).start()
    counter = 0
    for url, seg_list in doc_list:
        word_set = set(seg_list)
        for word in word_set:
            if word not in df_dict:
                df_dict[word] = 0
            df_dict[word] += 1                                          # word -> doc_count
        counter += 1
        progress.update(counter)
    progress.finish()
    print "aggregating df dict (word -> df) done"

    # dump df dict
    print "dumping template (index -> word) ..."
    with open("./df.json", 'w') as fd:
        fd.write(dumps(df_dict, indent=4, ensure_ascii=False))
    print "dumping template (index -> word) done"

    print "aggregating df dict (word -> idf) ..."
    idf_dict = {}
    
    progress = ProgressBar(maxval = len(df_dict)).start()
    counter = 0
    for word in df_dict:
        if df_dict[word] > 10:
            idf_dict[word] = log(float(len(doc_list)) / df_dict[word])               # word -> idf
        counter += 1
        progress.update(counter)
    progress.finish()
    word_list = list(idf_dict)
    word_dict = dict((word_list[index], index) for index in xrange(len(word_list)))  # word -> index
    index_dict = dict((index, word_list[index]) for index in xrange(len(word_list))) # index -> word
    print "aggregating idf dict (word -> idf) done"

    # dump index->word dict
    print "dumping template (index -> word) ..."
    with open(template_file, 'w') as fd:
        fd.write(dumps(index_dict, indent=4, ensure_ascii=False))
    print "dumping template (index -> word) done"

    # tfidf
    print "dumping feature ..."
    with open(data_file, 'w') as fd:
        progress = ProgressBar(maxval = len(doc_list)).start()
        counter = 0
        for url, seg_list in doc_list:
            tf_dict = {} 
            for word in seg_list:
                if word not in tf_dict:
                    tf_dict[word] = 0
                tf_dict[word] += 1 # word -> word_count
            for word in tf_dict:
                tf_dict[word] = float(tf_dict[word]) / len(seg_list)
                
            feature = [0] * len(word_list)
            for word in tf_dict:
                if (word in word_dict) and (word in idf_dict):
                    feature[word_dict[word]] = tf_dict[word] * idf_dict[word]
            fd.write("%s\t%s %d\n" % (url, " ".join([str(value) for value in feature]), url_dict[url]))
            counter += 1
            progress.update(counter)
        progress.finish()
    print "dumping feature done"
        
    # tf-idf transform
    #with open(data_file, 'w') as fd:
    #    progress = ProgressBar(maxval = len(doc_array.shape[0])).start()
    #    counter = 0
    #    for index in xrange(len(doc_array)):
    #        url = url_list[index]
    #        label = tag_dict[url_dict[url]]
    #        vector = " ".join([doc_array[index][i] for i in xrange(len(word_list))])
    #        fd.write("%s\t%s\t%d\n" % (url, vector, label))
    #        progress.update(counter)
    #    progress.finish()

if __name__ == "__main__":

    main()

