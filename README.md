# 学习网站
* https://github.com/sjas/assessing-mininet //可将topo转成mininet可识别的形式
* http://www.topology-zoo.org/toolset.html //topo zoo
* https://blog.csdn.net/xiajx98/article/month/2019/06 //虽然博客少，但写得都不错
* https://osrg.github.io/ryu-book/en/html/traffic_monitor.html //ryu中文资料
* https://book.ryu-sdn.org/zh_tw/Ryubook.pdf //同上
* https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html //doc
* https://www.cnblogs.com/ssyfj/p/11762093.html //山上有风景博客，写得不错

# ubutu
## ubuntu关闭自动锁屏

   关闭息屏，最后0是代表关闭锁屏，将0替换为60代表60s后自动息屏，以此类推。
    gsettings set org.gnome.desktop.session idle-delay 0
     
     
    关闭锁屏
    gsettings set org.gnome.desktop.screensaver lock-enabled false

# emacs常用命令
## 代码折叠
这里说的是emacs自带的HideShow mode.

进入HideShow mode： M-x hs-minor-mode（幸亏有tab键。。要不这么长的命令=。=）

主要的功能：

* C-c @ C-M-s 显示所有的代码
* C-c @ C-M-h 折叠所有的代码
* C-c @ C-s 显示当前代码区
* C-c @ C-h 折叠当前代码区
* C-c @ C-c 折叠/显示当前代码区

## 字体大小修改
放大字体: Ctrl-x Ctrl-+ 或 Ctrl-x Ctrl-=
缩小字体: Ctrl-x Ctrl–
重置字体: Ctrl-x Ctrl-0

## 在emacs中安装magit
取自:https://magit.vc/manual/magit/Installing-from-Melpa.html#Installing-from-Melpa
add one of the archives to package-archives:
To use Melpa: 
```
(require 'package)
(add-to-list 'package-archives
             '("melpa" . "http://melpa.org/packages/") t)
```
To use Melpa-Stable: 
```
(require 'package)
(add-to-list 'package-archives
             '("melpa-stable" . "http://stable.melpa.org/packages/") t)
```
Once you have added your preferred archive, you need to update the local package list using:

> M-x package-refresh-contents RET

Once you have done that, you can install Magit and its dependencies using:

> M-x package-install RET magit RET

## Emacs 中使用拼写检查
> M-x flyspell-mode  
若出现Error: No word lists can be found for the language "zh_CN"
则在.emacs中加入如下代码,指定其只用于检查英语即可
```
;; use apsell as ispell backend
(setq-default ispell-program-name "aspell")
;; use American English as ispell default dictionary
(ispell-change-dictionary "american" t)
```

## Emacs 中进行查找与替换
* 使用 M-% 开启查找替换模式
|使令|作用
|---|--
|y,[space] | 替换当前并到下一个
|n|忽略当前到下一个
|^|回到前一个匹配入
|q|退出

* M-x recursive-edit:递归编辑,再用C-M-c返回,没试成功.

