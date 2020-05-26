### 缘由

新一点的系统很多都是采用Vue、React之类的框架来做前端。使用了这些新框架的站点基本上都是前后端分离的，服务端渲染（Server Side Render）在大企业内有运用，但是中后台系统一般不会用到，这个技术更多被用在内容需要更加频繁变更或稳定控制的活动页面等偏向于前台的地方，中后台程序更多是看业务需求，一般大多数还是以前后端分离、XHR调API这种形式为主。

### 关于Webpack

不论是Vue还是React，Webpack都是不可或缺的一个工具，它可以在开发的过程中提供热更新，也可以在整个项目上线前完成最终针对生产环境的编译、打包工作。利用Webpack技术将JS类拓展语言进行打包，当然很多都是配套使用，例如Vue（前端Javascript框架）+Webpack技术；

以Vue站点为例，Webpack打包出来的东西，在JS上，主要有两个：

  * app.[hash].js
  * chunk-vendors.[hash].js

通常来说，chunk-vendor开头的文件是完全不需要我们去关注的，因为这个文件没有意义，里面包含的都是各种各样的依赖，除非你打算寻找的渗透点出在某个前端依赖上，否则chunk-vendor这个文件一般是不需要管的。页面本身的应用主要都在app.[hash].js里。

有的站点在打包后还会生成一个“manifest.[hash].js”，这个文件对于我们来说也有一定的价值，至于它是干什么用的，后面会提到。

对于打包生成的app.[hash].js，在默认情况下，它包括了这个项目前端所有的逻辑。

### 关于Source Map

这种技术也在普及，并且转向常态化，对渗透测试人员来说极其不友好：

  * 1.增加了前端代码阅读的时间（可读性很差） 

  * 2.由原因1间接造成了前端漏洞的审计困难性

但是也具备一定的好处：

  * 1.采用这种模式，后端接口将完全暴露在JS文件中

除此之外，如果生成了Source Map文件可以利用该文件还原网站原始前端代码（关于技术名词的具体含义请自行查询百科）


### 寻找思路

这种一般来说，前段加载的都比较少。利用requests去打开页面，然后寻找script src。找到对应的js文件。

找到js以后去找# sourceMappingURL=xxx.map 一般这个map如果可以访问必定可以还原出来

然后去解析这个map，它本质上是一个json文件，根据我们的需要把里面的sourcesContent保存下来

### 脚本使用

```
git clone https://github.com/0xa-saline/SourceMap_restore_source
cd SourceMap_restore_source
python3 mappings.py http://www.baidu.com/
2020-05-26 Tuesday 11:11:35 DEBUG 12985 check	http://www.baidu.com/js/app.f49d83e6.js
2020-05-26 Tuesday 11:11:35 DEBUG 12985 check	http://www.baidu.com/js/chunk-vendors.c8dc1ca1.js
2020-05-26 Tuesday 11:11:41 INFO 12985 http://www.baidu.com/js/app.f49d83e6.js	found sourceMappingURL
2020-05-26 Tuesday 11:11:43 INFO 12985 http://www.baidu.com/js/app.f49d83e6.js.map	success get mappings
```

![image](https://user-images.githubusercontent.com/14137698/82857902-e6620f00-9f44-11ea-9d0d-0578cc481040.png)

对应的文件会保存在当前host的文件夹内

```
├── 192.168.1.18
│   └── js
│       ├── app.cf578cc7.js
│       └── chunk-vendors.f837dbca.js
├── 192.168.1.68_8090
│   └── js
│       ├── app.14c99c88.js
│       └── chunk-vendors.c8222fea.js
├── 192.168.1.242_8088
│   └── static
│       └── js
│           ├── 7.6f33fbba.chunk.js
│           ├── 7.6f33fbba.chunk.js.map
│           ├── main.a29968b8.chunk.js
│           └── main.a29968b8.chunk.js.map
├── 192.168.1.139
│   └── js
│       ├── app.ef46941d.js
│       ├── app.ef46941d.js.map
│       ├── chunk-vendors.38f7f856.js
│       └── chunk-vendors.38f7f856.js.map
├── 192.168.1.218_5001
│   └── js
│       ├── app.65236379.js
│       ├── app.65236379.js.map
│       ├── chunk-vendors.554e271c.js
│       └── chunk-vendors.554e271c.js.map
```

### 还原代码

利用restore-source-tree 进行还原

原作者的有BUG，使用国外友人修复后的版本：https://github.com/laysent/restore-source-tree，安装步骤如下：

```
git clone https://github.com/laysent/restore-source-tree
cd restore-source-tree
sudo npm install -g
```

```
# -o 参数是指定输出目录，若不适用则为默认的output目录
restore-source-tree app.f49d83e6.js.map
```


### 参考
  
  * https://werhw.cn/2020/04/vue-panetrate/
  
  * https://gh0st.cn/archives/2020-01-08/2
  
  * https://laysent.com/til/2019-05-03_restore-source-map
  
  * [利用SourceMap还原前端代码](https://mp.weixin.qq.com/s?__biz=MzAxNDM3NTM0NQ==&mid=2657035959&idx=1&sn=8f65b8486972fd17f4a2b6c2c0080c01&chksm=803fc669b7484f7f480a580b926af4173694c842a169484f389bd0ba0759ea3b197796b7d51c)

