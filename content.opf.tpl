<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="bookid">
	<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
		<dc:title>Revolution in The Valley</dc:title>
		<dc:creator>Andy Hertzfeld</dc:creator>
		<dc:date>2004</dc:date>
		<dc:rights>Creative Commons Attribution-NonCommercial 1.0 Generic (CC BY-NC 1.0)</dc:rights>
		<dc:identifier opf:scheme="ISBN" id="bookid">urn:isbn:9781449386900</dc:identifier>
		<dc:language>en</dc:language>
		<meta name="cover" content="%(cover)s"/>
	</metadata>
	<manifest>
		<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
		<item id="css" href="folklore.css" media-type="text/css"/>
		<item id="itunes-metadata" href="../iTunesMetadata.plist" media-type="application/xml"/>
		%(files)s
	</manifest>
	<spine xmlns="http://www.idpf.org/2007/opf" toc="ncx">
		%(toc)s
	</spine>
</package>
