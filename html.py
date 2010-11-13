"""
Library to generate html in a declarative manner.
Needs polishing to be reusable..
"""

def out(s):
  print s

def preamble():
  return """<html>
<head>
<link rel=stylesheet type='text/css' href='static/tabs.css'/>
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"
        type="text/javascript"></script>
<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/jquery-ui.min.js"
        type="text/javascript"></script>
<link href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css"
      rel="stylesheet" type="text/css"/>
</head>
"""

def postamble():
  return "</html>"

def tag(name, s, **opts):
  optstr = ' '.join(map(lambda (k,v): '%s="%s"' % (k,v), opts.iteritems()))
  return "<%s %s>%s</%s>" % (name, optstr, s, name)

def ul(lst, **opts):
  s = "\n".join(map(lambda x: "<li>%s</li>"%x, lst))
  return tag("ul", s, **opts)

def anchor(s, **opts):
  return tag("a", s, **opts)

def div(s, **opts):
  return tag("div", s, **opts)
  return "<div id='%s'>%s</div>\n\n" % (i, s)

def tabs(lst, prefix='t'):
  """Construct tab from lst consisting of { 'title':.., 'content':..}"""
  tabcls = 'tabs'
  panecls = 'panes'
  tabs = ul(map(lambda (i,x):
                  anchor(x['title'],href='#%s%d'%(prefix,i)),
                enumerate(lst)),
            id='ul-%s'%(prefix))

  content_lst = map(lambda (i,x):
                      div(x['content'], id='%s%d'%(prefix,i)),
                    enumerate(lst))

  content = "\n".join(content_lst)

  return """<script>$(document).ready(function() {
    $("#tabs-%s").tabs();
  });
  </script>
  <div id="tabs-%s">
    %s
    %s
  </div>""" % (prefix, prefix, tabs, content)

def pre(s):
  return "<pre>%s</pre>" % s

def img(s):
  return "<img src='%s?' width='100%%'/>" % (s)

def aimg(s):
  """A linked image."""
  return anchor(img(s), href=s)

def html(s):
  return preamble() + s + postamble()

