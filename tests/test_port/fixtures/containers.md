named container with attributes
.
::::note {#n1 .lead title="Heads up"}
body
::::
.
<div class="container container-note lead" id="n1" title="Heads up">
<p>body</p>
</div>
.

container with block content
.
:::note
- a
- b

```py
code
```

> quote
:::
.
<div class="container container-note">
<ul>
<li>a</li>
<li>b</li>
</ul>
<pre><code class="language-py">code
</code></pre>
<blockquote>
<p>quote</p>
</blockquote>
</div>
.

nested containers
.
::::note
outer
:::tip
inner
:::
::::
.
<div class="container container-note">
<p>outer</p>
<div class="container container-tip">
<p>inner</p>
</div>
</div>
.

empty container
.
:::note
:::
after
.
<div class="container container-note"></div>
<p>after</p>
.

unclosed container is closed at the end of the parent block
.
:::note
body
.
<div class="container container-note">
<p>body</p>
</div>
.

indented colons are an indented code block
.
    :::note
    body
.
<pre><code>:::note
body
</code></pre>
.

container interrupts a paragraph
.
para
:::note
body
:::
.
<p>para</p>
<div class="container container-note">
<p>body</p>
</div>
.

trailing junk on the marker line
.
:::note extra
body
:::
.
<p>:::note extra
body</p>
<div class="container"></div>
.

invalid attribute block
.
:::note {bad attr!!}
body
:::
.
<p>:::note {bad attr!!}
body</p>
<div class="container"></div>
.

bare colon container
.
:::
text
:::
.
<div class="container">
<p>text</p>
</div>
.

nameless container with attributes
.
::: {.k}
text
:::
.
<div class="container k">
<p>text</p>
</div>
.

closing marker may be longer than the opening one
.
:::note
text
:::::
.
<div class="container container-note">
<p>text</p>
</div>
.

container in a list, closed by the parent block
.
- :::note
  text
- next
.
<ul>
<li>
<div class="container container-note">
<p>text</p>
</div>
</li>
<li>next</li>
</ul>
.

attribute span
.
[文字]{#a .k lang=zh}
.
<p><span class="k" id="a" lang="zh">文字</span></p>
.

span wins over a reference link
.
[foo]{.k}

[foo]: /url
.
<p><span class="k">foo</span></p>
.

inline link followed by literal braces
.
[foo](/u){.k}
.
<p><a href="/u">foo</a>{.k}</p>
.

span with nested inline content
.
[*em* `code`]{.k}
.
<p><span class="k"><em>em</em> <code>code</code></span></p>
.

span with invalid attribute block
.
[foo]{bad attr!!}
.
<p>[foo]{bad attr!!}</p>
.

empty attribute block
.
[foo]{}
.
<p><span>foo</span></p>
.
