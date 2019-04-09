from tqdm import tqdm
import csv
import re
import argparse
import os
import sys
from collections import defaultdict

reload(sys)
sys.setdefaultencoding("utf8")


def get_movies_db(path):
    with open(path, "r") as f:
        reader = csv.reader(f)
        id2movie = {}
        for row in reader:
            if row[0] != "index":
                # separate the title into movieName and movieYear if present
                pattern = re.compile("(.+)\((\d+)\)")
                match = re.search(pattern, row[1])
                if match is not None:
                    # movie Year found
                    content = (match.group(1).strip(), match.group(2))
                else:
                    # movie Year not found
                    content = (row[1].strip(), None)
                id2movie[int(row[0])] = content
    print("loaded {} movies from {}".format(len(id2movie), path))
    return id2movie


def get_wiki(path):
    wiki = {}
    wiki_name = defaultdict(list)
    with open(path, "r") as f:
        pages = f.read().strip().split("\n\n")
        for page in pages:
            page = page.split("\n")
            title, article = page[0], page[1:]
            title = title[2:]
            article = " ".join([line[2:] for line in article])

            # find released year
            pattern = re.compile("(.+)\(.*(\d+).*\)")
            match = re.search(pattern, title)
            if match is not None:
                pattern = re.compile("\d{4}")
                match = re.findall(pattern, title)
                year = match[0]
            else:
                # if not found in title, find in the article
                pattern = re.compile("\d{4}")
                match = re.findall(pattern, article)
                if match:
                    year = match[0]
                else:
                    year = None

            # finally, remove parentheses in title
            pattern = re.compile("(.+)( \(.*\))")
            match = re.search(pattern, title)
            if match:
                title = match.group(1)

            # has same name and same year conflicts
            wiki_name[title].append((year, article))
            if (title, year) not in wiki or len(article) > len(wiki[(title, year)]):
                wiki[(title, year)] = article
    return wiki, wiki_name


def match(db_path, wiki_path, write_to):
    """
    For each movie in db, find equivalent movie name in wikimovies.
    Writes to a csv file: dbId, movieName, dbId, movielensId, wiki
    :param db_path:
    :param wiki_path:
    :param write_to:
    :return:
    """
    movies_db = get_movies_db(db_path)
    movies_wiki, movies_wiki_name = get_wiki(wiki_path)
    matched_movies = {}

    total_exact_matches = 0
    total_name_matches = 0
    f = open(write_to, "w")
    for movieId, (db_name, year) in tqdm(movies_db.items()):
        # first find (name, year) exact match
        article = ""
        if (db_name, year) in movies_wiki:
            total_exact_matches += 1
            article = movies_wiki[(db_name, year)]
        # if not found, and year is None, match only the movie name
        elif db_name in movies_wiki_name:
            if (len(movies_wiki_name[db_name]) == 1) and (
                (year is None) or (movies_wiki_name[db_name][0][0] is None)
            ):
                total_name_matches += 1
                article = movies_wiki_name[db_name][0][1]
        f.write(article + "\n")

    print(
        "Over {} movies mentioned in ReDial, {} of them are perfectly matched, {} of them matched by name".format(
            len(movies_db), total_exact_matches, total_name_matches
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies_merged_path")
    parser.add_argument("--wiki_path")
    parser.add_argument("--destination", default="redial/movies_wiki.csv")
    args = parser.parse_args()
    match(args.movies_merged_path, args.wiki_path, args.destination)
