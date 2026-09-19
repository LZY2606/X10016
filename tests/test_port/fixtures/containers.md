Basic container
.
:::note
content
:::
.
<div class="container container-note">
<p>content</p>
</div>
.

Container with attributes
.
::::note {#n1 .lead title="Heads up"}
content
::::
.
<div class="container container-note lead" id="n1" title="Heads up">
<p>content</p>
</div>
.

Unnamed container
.
:::
content
:::
.
<div class="container">
<p>content</p>
</div>
.

Empty container
.
:::note
:::
after
.
<div class="container container-note"></div>
<p>after</p>
.

Unclosed container is closed by the end of the parent block
.
:::note
content
.
<div class="container container-note">
<p>content</p>
</div>
.

Closing marker may be longer than the opening one
.
:::note
content
::::::
.
<div class="container container-note">
<p>content</p>
</div>
.

Nested containers
.
::::outer
:::tip
inner
:::
::::
.
<div class="container container-outer">
<div class="container container-tip">
<p>inner</p>
</div>
</div>
.

Container with block content
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

Container interrupts a paragraph
.
para
:::note
content
:::
.
<p>para</p>
<div class="container container-note">
<p>content</p>
</div>
.

Opening line with trailing text is not a container
.
:::note junk
.
<p>:::note junk</p>
.

Invalid attribute block is not a container
.
:::note {bad!!}
.
<p>:::note {bad!!}</p>
.

Indented by four spaces is a code block
.
    :::note
    content
.
<pre><code>:::note
content
</code></pre>
.

Container inside a blockquote
.
> ::::note {#n1 .lead title="Heads up"}
> ok *em* and [tag]{.k}
>
> :::tip
> :::
> ::::
.
<blockquote>
<div class="container container-note lead" id="n1" title="Heads up">
<p>ok <em>em</em> and <span class="k">tag</span></p>
<div class="container container-tip"></div>
</div>
</blockquote>
.

Attribute span
.
[text]{#a .k lang=zh}
.
<p><span id="a" class="k" lang="zh">text</span></p>
.

Attribute span with inline content
.
[a *b* `c`]{.k}
.
<p><span class="k">a <em>b</em> <code>c</code></span></p>
.

Attribute span wins over a reference link
.
[foo]{.k}

[foo]: /u
.
<p><span class="k">foo</span></p>
.

Inline link is not a span
.
[foo](/u){.k}
.
<p><a href="/u">foo</a>{.k}</p>
.

Invalid attribute block after a bracket span is literal text
.
[foo]{bad!!}
.
<p>[foo]{bad!!}</p>
.
