import urllib2
import urllib
import urlparse
import os.path
import datetime


MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}
LINK_START_TAG = '<a href="StoryView.py?'
LINK_END_TAG = '">'

stories_filenames = set()

for offset in [0, 60]:
    data = None
    cache_filename = 'index-%d.html' % offset

    if not os.path.exists(cache_filename):
        print 'Downloading stories with offset %d' % offset
        data = urllib2.urlopen('http://www.folklore.org/ProjectView.py?project=Macintosh&index=%d&detail=low' % offset).read()

        with open(cache_filename, 'w') as cache:
            cache.write(data)
    else:
        with open(cache_filename) as cache:
            data = cache.read()

    # Look for <a href="StoryView.py?project=Macintosh&story=I'll_Be_Your_Best_Friend.txt&sortOrder=Sort by Date&detail=low">
    print 'Parsing stories with offset %d' % offset
    start = data.find(LINK_START_TAG)

    while start != -1:
        data = data[start:]
        end = data.find(LINK_END_TAG)
        link = urlparse.parse_qs(data[len(LINK_START_TAG):end])

        if link['project'][0] != 'Macintosh':
            raise Exception('Stories should be about Macintosh')

        stories_filenames.add(link['story'][0])
        data = data[end:]
        start = data.find(LINK_START_TAG)

print 'Found %d stories' % len(stories_filenames)
stories = []

for story_filename in stories_filenames:
    data = None

    if not os.path.exists(story_filename):
        url = 'http://www.folklore.org/projects/Macintosh/%s' % urllib.quote(story_filename)
        print 'Downloading %s' % story_filename
        data = urllib2.urlopen(url).read()

        with open(story_filename, 'w') as story_file:
            story_file.write(data)
    else:
        with open(story_filename) as story_file:
            data = story_file.read()

    data = data.replace('\r\n', '\n')

    print 'Parsing %s' % story_filename
    story = {}
    header, content = data.split('\n\n', 1)

    # Look for Project: Macintosh
    for line in header.split('\n'):
        key, value = line.split(': ', 1)
        story[key] = value

    date = story['Date']
    if date == 'undated':
        story['ParsedDate'] = datetime.date(1990, 1, 1)
    else:
        date_components = date.split(' ')

        if len(date_components) == 1:
            story['ParsedDate'] = datetime.date(int(date), 6, 1)
        else:
            month, year = date_components
            story['ParsedDate'] = datetime.date(int(year), MONTHS[month], 2)

    for key in ['Characters', 'Topics']:
        if story.has_key(key):
            story[key] = story[key].split(',')

    if story.has_key('Image'):
        image_filename = story['Image']

        if not os.path.exists(image_filename):
            print 'Downloading %s' % image_filename

            with open(image_filename, 'w') as image_file:
                url = 'http://folklore.org/projects/Macintosh/images/%s' % urllib.quote(image_filename)
                image_file.write(urllib2.urlopen(url).read())

    story['Content'] = content
    stories.append(story)

    stories.append(story)

for story in sorted(stories, key=lambda story: story['ParsedDate']):
    print '%s (%s)' % (story['Title'], story['Date'])
