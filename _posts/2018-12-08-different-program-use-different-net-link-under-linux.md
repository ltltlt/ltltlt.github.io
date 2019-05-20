---
layout: default
title: "Different program use different net link under Linux"
categories: Nginx
---
- [Why](#why)
- [What](#what)
- [How](#how)
  - [Add a net namespace](#add-a-net-namespace)
  - [Add net link to namespace](#add-net-link-to-namespace)
  - ["Into" this net namespace](#%22into%22-this-net-namespace)
  - [Check if net link added to this net namespace successfully](#check-if-net-link-added-to-this-net-namespace-successfully)
  - [Connect to wifi(if you use wireless net link)](#connect-to-wifiif-you-use-wireless-net-link)
  - [Bind a network address](#bind-a-network-address)
  - [Check if you can access the extranet](#check-if-you-can-access-the-extranet)
  - [Check if dns look up works well](#check-if-dns-look-up-works-well)
  - [Change dns server if necessary](#change-dns-server-if-necessary)
  - [After all this, you mostly done](#after-all-this-you-mostly-done)
- [Foreign link(reference)](#foreign-linkreference)

## Why

  Sometimes, you may want your program use one specific net device, because your net devices have different network access abilities.
  For me, I have two demands:

  1. I want to use IRC in company network, and i don't want company to know that(i need to connect to irc.freenode.net, and IRC uses unique(?) data). But for some program, it need company's network to access company's intranet.
  2. Almost all traffic in my home go through VPS, but sometimes i need to download BT resources, these traffic cannot go through, since my VPS have flow limitation and not welcome BT.

## What

  The approach mentioned here can let different program use different net link. Some programs can use company's intranet, other programs don't. All my work is done under Archlinux, you can easily change it to other linux distributions, but not Windows, if you need to do this under Windows, you may need to check reference of this post.

## How

### Add a net namespace

```zsh
ip netns add $netns
```

### Add net link to namespace

If you use wired device

```zsh
ip link set $net_link netns $netns
```

If you use wireless device

```zsh
iw phy $phy set netns name $netns    # you can check your $phy using command `iw list`
```

### "Into" this net namespace

```zsh
ip netns exec $netns sudo -u $your_user_name bash    # i use zsh
```

### Check if net link added to this net namespace successfully

```zsh
ip link
```

### Connect to wifi(if you use wireless net link)

```zsh
wpa_supplicant -i $net_link -c $wpa_supplicant_config_file &
```

Note that all commands below is execute under this net namespace

### Bind a network address

Since dhcpcd(or dhcpclient) cannot work under net namespace(I cannot, maybe you can, use `dhcpcd $net_link` then `ifconfig` to check if this net link have a address now), i need to bind a address for it manually.

```zsh
ifconfig $net_link $ip
```

### Check if you can access the extranet

```zsh
ping 8.8.8.8
```

If you cannot, you may need to set route use following command:

```zsh
route add default gw $gateway $net_link
```

### Check if dns look up works well

```zsh
dig www.google.com    # or just `ping www.google.com`
```

If ping success, you done. If not, you may need to change dns server manually.(the reason is quite simple, your dns server is mostly point to gateway, but different net link have different gateway address, it can be 192.168.1.1 or 172.17.1.1 or whatever, if your dns lookup fail, it may because your dns server change)

### Change dns server if necessary

Since your dns server is written in /etc/resolve.conf, you may want to change it directly, but it won't work, because dhcpcd will overwrite it. Different linux distribution have different approach to solve this. Under Archlinux, you can edit /etc/resolve.conf.head, add `nameserver 8.8.8.8` or something whatever like this into it.

### After all this, you mostly done

You may need to check using `curl ip.sb` to see if your ip address change.

## Foreign link(reference)

This post is mostly based on [this answer](https://unix.stackexchange.com/questions/210982/bind-unix-program-to-specific-network-interface#answer-210992).
Check [this answer](https://superuser.com/questions/241178/how-to-use-different-network-interfaces-for-different-processes#answer-241200) for another approach(I use this approach but for some reason this doesn't work).
[This post](https://cizixs.com/2017/02/10/network-virtualization-network-namespace/) tells me a lot about linux net namespace.
[This answer](https://superuser.com/questions/653996/how-to-move-wireless-connection-to-other-network-namespace#answer-901438) helps me to add a wireless net link into net namespace.
[Archwiki](https://wiki.archlinux.org/index.php/Resolv.conf_(%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87)) gives me hint about how to change dns server.
For how to connect to a wifi under linux terminal or more wireless network configuration, you may need to check [this](https://wiki.archlinux.org/index.php/Wireless_network_configuration), [this link](https://linux.cn/article-4015-1.html) helps me a lot of time too.