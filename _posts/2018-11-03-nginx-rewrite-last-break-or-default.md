---
layout: default
title: "Nginx rewrite: last, break or default"
categories: Nginx
---
- [前言](#%E5%89%8D%E8%A8%80)
- [预备知识](#%E9%A2%84%E5%A4%87%E7%9F%A5%E8%AF%86)
- [rewrite指令中默认，last和break的区别](#rewrite%E6%8C%87%E4%BB%A4%E4%B8%AD%E9%BB%98%E8%AE%A4last%E5%92%8Cbreak%E7%9A%84%E5%8C%BA%E5%88%AB)
- [例子证明](#%E4%BE%8B%E5%AD%90%E8%AF%81%E6%98%8E)
  - [break](#break)
  - [last](#last)
  - [empty](#empty)
- [参考资料](#%E5%8F%82%E8%80%83%E8%B5%84%E6%96%99)

## 前言

  最近了解了一些nginx的知识，上网查看了一些资料，特此做一些分享。  
  这篇博客不会特别说到nginx配置的执行过程和nginx里的变量，如果有需要了解，可参考:
  [agentzh 的 Nginx 教程](https://openresty.org/download/agentzh-nginx-tutorials-zhcn.html)。  
  这篇博客里的许多推导也来自上面的链接，如果有误，请与我联系。

## 预备知识

  1. 首先明确一点，rewrite指令来自ngx_http_rewrite_module，此模块中的所有指令若是在server块内location块外，会执行于server-rewrite阶段；如果位于location块内，会执行于rewrite阶段。此模块中的所有指令都不会执行在其他阶段。
  2. nginx执行阶段如下所示：  

     - post-read
     - server-rewrite
     - find-config
     - rewrite
     - post-rewrite
     - preaccess
     - access
     - post-access
     - try-files
     - content
     - log

  3. 不同的模块在同一阶段中执行的顺序不定，同一阶段中的rewrite指令执行顺序是确定的，这是由于其都在同一个模块ngx_http_rewrite_module中定义。rewrite阶段的一些指令是顺序执行，即使属于不同模块，这是这些第三方模块将指令注入ngx_http_rewrite_module中实现的。  
  4. 内部跳转是发生在post-rewrite阶段而不是rewrite阶段，并且是跳到find-config阶段重新匹配location块。  
  5. ngx_http_rewrite_module中的指令break的作用是停止处理此阶段中其他ngx_http_rewrite_module模块中的的指令（但不会停止处理此phase中其他模块中的指令，除非指令是嵌入到ngx_http_rewrite_module模块中执行的）。  
  6. rewrite指令中，last，break和rewrite都不会修改浏览器地址栏，只有回送3xx给浏览器且设置了location header才会修改，也就是说permanent与redirect会修改。  

## rewrite指令中默认，last和break的区别

  last和break都会跳过此阶段中其他ngx_http_rewrite_module中的指令（directive），而rewrite指令默认不会跳过任何指令。
  last，break和默认都会重写(rewrite) $uri 这个预定义变量为新写入的uri，而不会修改 $request_uri 这个变量，这是因为 $request_uri 这个变量是不可写的，总是包含客户端一开始请求的uri，而 $uri 这个变量总是包含当前实时的uri。  
  last会使得在post-rewrite阶段，会跳到find-config阶段重新匹配location，而break不会。  
  `nginx a b break；` 相当于 `nginx a b；break；` 。  
  如果rewrite指令位于server块内location块外，那么last和break没有区别。这是因为这两条指令都会跳过ngx_http_rewrite_module模块在此阶段的其他指令，而且都会修改uri，最后都得执行find-config，而find-config是根据uri进行location匹配的。  
  在location块内，写last需要小心，因为之后在post-rewrite会跳到find-config阶段，如果操作不慎会死循环，而nginx在10次循环后会直接返回500。如下例所示（例子修改自[ngx_http_rewrite_module官方文档](http://nginx.org/en/docs/http/ngx_http_rewrite_module.html#rewrite)）：  

```nginx
location /download/ {
    rewrite ^(/download/.*)/media/(.*)\..*$ $1/mp3/$2.mp3 last;
    rewrite ^(/download/.*)/audio/(.*)\..*$ $1/mp3/$2.ra  last;
    return  403;
}
```

## 例子证明

  如果读者想要复现，请使用openresty（我是这么做的）或者自己安装一些第三方模块。

### break

```nginx
server {
    # ...
    listen 8080;
    default_type text/plain;
    location = / {
        echo "var is: $var";
        echo "var1 is: $var1";
        echo "uri is: $uri";
        echo "request_uri is: $request_uri";
        set $var abc;
        set $var1 abc;
        rewrite ^ /foo break;
        set_by_lua "ngx.var.var='bcd'";
        rewrite_by_lua "ngx.var.var1='bcd'";
    }
    location = /foo {
        echo "foo";
    }
}
```

  访问localhost:8080会得到:

  ```markup
  var is: abc
  var1 is: bcd
  uri is: /foo
  request_uri is: /
  ```

- 可以看出rewrite指令确实成功重写了uri，但不会影响request_uri。`rewrite ... break` 指令并不会跳到其他location（即不会重新执行find-config阶段）。
- var变量的值为abc而不是空，是因为echo指令在content阶段执行，晚于rewrite，所以即使此指令写在前面，也会晚于rewrite阶段的指令执行。
- var变量的值不是 `set_by_lua` 指定的bcd是因为 `rewrite ... break;` 跳过了剩下的rewrite模块中的指令，虽然set_by_lua指令并不在rewrite模块中，但其作者为了使此指令能与ngx_http_rewrite_module模块中定义的指令顺序执行而不是随机执行，将其指令“注入”到了ngx_http_rewrite_module模块的指令序列中，所以 `set_by_lua` 指令也被break所跳过。下面一段引用自[agentzsh 的 Nginx 教程](https://openresty.org/download/agentzh-nginx-tutorials-zhcn.html#02-NginxDirectiveExecOrder05):
    > 标准 ngx_rewrite 模块的应用是如此广泛，所以能够和它的配置指令混合使用的第三方模块是幸运的。事实上，上面提到的这些第三方模块都采用了特殊的技术，将它们自己的配置指令“注入”到了 ngx_rewrite 模块的指令序列中（它们都借助了 Marcus Clyne 编写的第三方模块 ngx_devel_kit）。换句话说，更多常规的在 Nginx 的 rewrite 阶段注册和运行指令的第三方模块就没那么幸运了。这些“常规模块”的指令虽然也运行在 rewrite 阶段，但其配置指令和 ngx_rewrite 模块（以及同一阶段内的其他模块）都是分开独立执行的。在运行时，不同模块的配置指令集之间的先后顺序一般是不确定的（严格来说，一般是由模块的加载顺序决定的，但也有例外的情况）。比如 A 和 B 两个模块都在 rewrite 阶段运行指令，于是要么是 A 模块的所有指令全部执行完再执行 B 模块的那些指令，要么就是反过来，把 B 的指令全部执行完，再去运行 A 的指令。除非模块的文档中有明确的交待，否则用户一般不应编写依赖于此种不确定顺序的配置。
- var1变量的值成功更新: 这是因为指令 `rewrite_by_lua` 不是注入到ngx_http_rewrite_module中执行，而是总在rewrite阶段的最后执行，这说明了 `rewrite ... break;` 指令并不会直接跳到post-rewrite阶段，而是继续执行rewrite阶段中不属于ngx_http_rewrite_module模块的指令。

***

### last

```nginx
server {
    # ...
    listen 8080;
    default_type text/plain;
    location = / {
        rewrite ^ /foo last;
        rewrite ^ /bar;
    }
    location = /foo {
        echo "foo";
    }
    location = /bar {
        echo "bar";
    }
}
```

  访问localhost:8080得到：

  ```markup
  foo
  ```

  可以看出，第一条 `rewrite ... last` 跳过了第二条rewrite，所以最后的uri是/foo。

***

### empty

```nginx
    server {
        # ...
        listen 8080;
        default_type text/plain;
        location = / {
            rewrite ^ /foo;
            rewrite ^ /bar;
        }
        location = /foo {
            echo "foo";
        }
        location = /bar {
            echo "bar";
        }
    }
```

  访问localhost:8080得到：

  ```markup
  bar
  ```

  这是因为默认的rewrite指令不会跳过其他ngx_http_rewrite_module的指令。

## 参考资料

- [agentzh's nginx tutorials](https://openresty.org/download/agentzh-nginx-tutorials-zhcn.html)
- [nginx official docs](http://nginx.org/en/docs/http/ngx_http_rewrite_module.html)
