# wx2lark
微信消息转发飞书，时间有限来不及整理，简单说一下怎么使用
1. 首先建议使用docker跑起来服务，先在自己的机器上安装docker环境
2. 然后进入代码目录执行docker build -t push .
3. 接着修改efb_wechat_slave目录下的send_lark.py文件，填写里面webhook_url_group和webhook_url_private，这两个需要在飞书中建一个只有你自己的群，拉机器人进去查看webhook地址
4. 成功后执行 chmod +x start.sh;./start.sh
5. 执行docker logs -f push后可以看到二维码，扫描登录微信就可以了
6. 到这个步骤微信收到的消息会转发到有机器人的那个群，这样就可以关了手机的微信后台了，飞书是支持鸿蒙推送、小米推送等等，只要把飞书的推送打开就行了也不用飞书后台

注意我这里其实已经实现了飞书发消息到微信，时间有限教程后面补，还是有点麻烦的且需要公司权限。
