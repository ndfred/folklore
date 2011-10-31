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
        url = 'http://www.folklore.org/projects/Macintosh/%s' % urllib.quote_plus(story_filename)
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
        story['Date'] = datetime.date(1990, 1, 1)
    else:
        date_components = date.split(' ')

        if len(date_components) == 1:
            story['Date'] = datetime.date(int(date), 6, 1)
        else:
            month, year = date_components
            story['Date'] = datetime.date(int(year), MONTHS[month], 2)

    for key in ['Characters', 'Topics']:
        if story.has_key(key):
            story[key] = story[key].split(',')

    story['Content'] = content
    stories.append(story)

for story in sorted(stories, key=lambda story: story['Date']):
    date = story['Date']
    if date == datetime.date(1990, 1, 1):
        date = 'unknown'
    elif date.day == 1:
        date = str(date.year)
    else:
        month = [month for month, index in MONTHS.iteritems() if index == date.month][0]
        date = '%s %d' % (month, date.year)

    print '%s (%s)' % (story['Title'], date)
