import urllib2
import urllib
import urlparse
import os.path
import datetime
import codecs


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


def fetch_story_links(data):
    # Look for <a href="StoryView.py?project=Macintosh&story=I'll_Be_Your_Best_Friend.txt&sortOrder=Sort by Date&detail=low">
    start_tag = '<a href="StoryView.py?'
    end_tag = '">'
    stories_filenames = set()
    start = data.find(start_tag)

    while start != -1:
        data = data[start:]
        end = data.find(end_tag)
        link = urlparse.parse_qs(data[len(start_tag):end])

        if link['project'][0] != 'Macintosh':
            raise Exception('Stories should be about Macintosh')

        stories_filenames.add(link['story'][0])
        data = data[end:]
        start = data.find(start_tag)

    return stories_filenames


def fetch_stories():
    stories_filenames = set()
    offset = 0

    while True:
        data = None
        cache_filename = 'index-%d.html' % offset

        if not os.path.exists(cache_filename):
            print 'Downloading stories with offset %d' % offset
            data = urllib2.urlopen('http://www.folklore.org/ProjectView.py?project=Macintosh&index=%d&detail=low' % offset).read()

            with codecs.open(cache_filename, 'w', 'utf8') as cache:
                cache.write(data)
        else:
            with codecs.open(cache_filename, 'r', 'utf8') as cache:
                data = cache.read()

        page_stories_filenames = fetch_story_links(data)

        if stories_filenames.issuperset(page_stories_filenames):
            break
        else:
            offset += 60
            stories_filenames.update(fetch_story_links(data))

    return stories_filenames


def parse_story_content(content):
    html_content_lines = []

    for line in content.split('\n'):
        stripped_line = line.strip()

        if stripped_line != '':
            # [image:polaroids/polaroids.1.jpg]
            # [image:bomb_icon.jpg::hspace=12 vspace=12 align=left]
            # [story:Round Rects Are Everywhere!]
            # [image:early_macpaint.jpg:An early screenshot of a half-implemented MacPaint]
            # [image:mousepaint.jpg:Bill Budge's MousePaint:align=left hspace=8]
            # [link:here.:http//www.amazon.com/exec/obidos/asin/0596007191/ref=nosim/folklore-20]
            html_content_lines.append('<p>%s</p>' % stripped_line)

    return '\n\n'.join(html_content_lines)


def parse_story(data):
    story = {}
    image_filenames = set()
    header, content = data.split('\n\n', 1)

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
            story[key] = frozenset(story[key].split(','))

    if story.has_key('Image'):
        image_filenames.add(story['Image'])

    story['Content'] = content
    story['HTMLContent'] = parse_story_content(content)

    return story, image_filenames


def parse_stories(stories_filenames):
    stories = []
    image_filenames = set()

    for story_filename in stories_filenames:
        data = None

        if not os.path.exists(story_filename):
            url = 'http://www.folklore.org/projects/Macintosh/%s' % urllib.quote(story_filename)
            print 'Downloading %s' % story_filename
            data = urllib2.urlopen(url).read()

            with codecs.open(story_filename, 'w', 'utf8') as story_file:
                story_file.write(data)
        else:
            with codecs.open(story_filename, 'r', 'utf8') as story_file:
                data = story_file.read()

        data = data.replace('\r\n', '\n')

        story, story_image_filenames = parse_story(data)
        image_filenames.update(story_image_filenames)

        stories.append(story)

    return stories, image_filenames


def download_images(image_filenames):
    for image_filename in image_filenames:
        if not os.path.exists(image_filename):
            print 'Downloading %s' % image_filename

            with open(image_filename, 'w') as image_file:
                url = 'http://folklore.org/projects/Macintosh/images/%s' % urllib.quote(image_filename)
                image_file.write(urllib2.urlopen(url).read())


def build_book():
    stories_filenames = fetch_stories()
    print 'Found %d stories' % len(stories_filenames)
    stories, image_filenames = parse_stories(stories_filenames)
    download_images(image_filenames)

    for story in sorted(stories, key=lambda story: story['ParsedDate']):
        print ' * %s (%s)' % (story['Title'], story['Date'])


if __name__ == '__main__':
    build_book()