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


def local_image_filename(image_filename):
    return image_filename.replace('/', ' - ')


def parse_story_content_tag(tag, content, stories_urls):
    components = content.split(':')
    components_count = len(components)

    if tag == 'image':
        image_filename = components[0]
        components[0] = urllib.quote(local_image_filename(components[0]))

        if components_count == 1:
            return '<div class="image"><img src="%s"></div>' % components[0], image_filename
        elif components_count == 2:
            return '<div class="image"><img src="%s"><p>%s</p></div>' % tuple(components), image_filename
        elif components_count == 3:
            css_class = ''
            description = ''

            if components[2].startswith('align=left'):
                css_class = ' float-left'

            if components[1] != '':
                description = '<p>%s</p>' % components[1]

            return '<div class="image%s"><img src="%s">%s</div>' % (css_class, components[0], description), image_filename
        else:
            raise Exception('Wrong arguments for an image tag: %s', content)
    elif tag == 'story':
        if components_count == 1:
            content = content.strip()

            if stories_urls.has_key(content):
                return '(see <a href="%s">%s</a>)' % (urllib.quote(stories_urls[content]), content)
            else:
                print 'Could not find the story to link to: %s' % repr(content)
                return ''
        else:
            raise Exception('Wrong arguments for a story tag: %s', content)
    elif tag == 'link':
        if components_count == 2:
            return '<a href="%s">%s</a>' % (components[1], components[0])
        else:
            raise Exception('Wrong arguments for a link tag: %s', content)


def parse_story_content(story, stories_urls):
    content = story['Content']
    html_content_lines = []
    image_filenames = set()

    if story.has_key('Image'):
        if story.has_key('Caption'):
            content = '%s%s' % ('[image:%s:%s:align=left]' % (story['Image'], story['Caption']), content)
        else:
            content = '%s%s' % ('[image:%s::align=left]' % story['Image'], content)

    for line in content.split('\n'):
        line = line.strip()

        if line != '':
            for tag in ['image', 'story', 'link']:
                start_tag = '[%s:' % tag
                end_tag = ']'
                components = []
                start = line.find(start_tag)

                while start != -1:
                    if start > 0:
                        components.append(line[:start])

                    line = line[start + len(start_tag):]
                    end = line.find(end_tag)
                    html = None

                    if tag == 'image':
                        html, image_filename = parse_story_content_tag(tag, line[:end], stories_urls)
                        image_filenames.add(image_filename)
                    else:
                        html = parse_story_content_tag(tag, line[:end], stories_urls)

                    components.append(html)
                    line = line[end + len(end_tag):]
                    start = line.find(start_tag)

                components.append(line)
                line = ''.join(components)

            html_content_lines.append('<p>%s</p>' % line)

    return '\n\n'.join(html_content_lines), image_filenames


def parse_story(data):
    story = {}
    image_filename = None
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
        image_filename = story['Image']

    story['Content'] = content

    return story, image_filename


def parse_stories(stories_filenames):
    stories = []
    stories_urls = {}
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

        story, story_image_filename = parse_story(data)
        story['Filename'] = story_filename
        story['HTMLFilename'] = '%s.html' % story['Filename'][:-4]
        story['URL'] = urllib.quote(story['HTMLFilename'])

        if story_image_filename:
            image_filenames.add(story_image_filename)

        stories_urls[story['Title']] = story['URL']
        stories.append(story)

    for story in stories:
        story['HTMLContent'], content_image_filenames = parse_story_content(story, stories_urls)
        image_filenames.update(content_image_filenames)

    return stories, image_filenames


def download_images(image_filenames):
    for image_filename in image_filenames:
        local_filename = local_image_filename(image_filename)

        if not os.path.exists(local_filename):
            print 'Downloading %s' % image_filename

            with open(local_filename, 'w') as image_file:
                url = 'http://folklore.org/projects/Macintosh/images/%s' % urllib.quote(image_filename)
                image_file.write(urllib2.urlopen(url).read())


def build_html(stories):
    template = None
    stories_html_components = []

    with codecs.open('folklore.tpl', 'r', 'utf8') as template_file:
        template = template_file.read()

    sorted_stories = sorted(stories, key=lambda story: story['ParsedDate'])

    for story_index in xrange(len(sorted_stories)):
        story = sorted_stories[story_index].copy()
        footer_components = []

        if story_index > 0:
            footer_components.append('&lt; <a href="%(URL)s">%(Title)s</a>' % sorted_stories[story_index - 1])

        footer_components.append('<a href="Stories.html">Back to the stories</a>')

        if story_index < len(stories) - 1:
            footer_components.append('<a href="%(URL)s">%(Title)s</a> &gt;' % sorted_stories[story_index + 1])

        print ' * %(Title)s (%(Date)s)' % story
        story['HTMLContent'] += '\n\n<p class="footer">%s</p>' % ' - '.join(footer_components)
        stories_html_components.append('<li><a href="%(URL)s">%(Title)s</a></li>' % story)

        with codecs.open(story['HTMLFilename'], 'w', 'utf8') as story_html_file:
            story_html_file.write(template % story)

    with codecs.open('Stories.html', 'w', 'utf8') as stories_html_file:
        stories_html_file.write(template % {
            'Title': 'folklore.org',
            'HTMLContent': '<p>%s</p>' % '\n'.join(stories_html_components)
        })


def build_book():
    stories_filenames = fetch_stories()
    print 'Found %d stories' % len(stories_filenames)
    stories, image_filenames = parse_stories(stories_filenames)
    download_images(image_filenames)
    build_html(stories)


if __name__ == '__main__':
    build_book()
