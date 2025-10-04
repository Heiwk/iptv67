import requests
import re
from collections import defaultdict

# =============================================
# 新手注意：这里是频道分类区域，可以按需修改
# =============================================

# 频道分类（正规区域）
CHANNEL_CATEGORIES = {
    "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                 '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '北京纪实科教',
                 '卫生健康','电视指南'],
    "卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视',
                 '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视',
                 '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视',
                 '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育',
                 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育'],
    "港澳频道": ['凤凰中文', '凤凰资讯', '凤凰香港','凤凰电影'],
    "电影频道": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场','星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影','超级电影'],
    "儿童频道": ['动漫秀场', '哒啵电竞', '黑莓电影', '黑莓动画','卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通'],             
    "iHOT频道": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教',
                 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈','iHOT爱科学', 'iHOT爱动漫'],  
    "综合频道": ['淘4K', '淘娱乐', '淘Baby', '萌宠TV', '北京纪实科教', '重温经典','CHANNEL[V]', '求索纪录', '求索科学', '求索生活',
                 '求索动物','睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论',
                 '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云',
                 '动漫秀场', '金色学堂', '法治天地', '哒啵赛事', '哒啵电竞'],
    "体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'], 
    "剧场频道": [ '古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧','超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠',  '怡伴健康',], 
}

# =============================================
# 新手注意：这里是频道名称映射区域，可以按需添加别名
# =============================================

# 频道映射（别名 -> 规范名）
CHANNEL_MAPPING = {
    # 这里包含很多频道名称映射，保持您原有的映射不变
    # 示例：
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV-1 综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV-2 财经"],
    # ... 您原有的映射内容保持不变
}

# =============================================
# 新手注意：这里是核心配置区域，需要重点关注
# =============================================

# 正则表达式 - 匹配IPv4和IPv6地址
ipv4_regex = r"http://\d+\.\d+\.\d+\.\d+(?::\d+)?"
ipv6_regex = r"http://\[[0-9a-fA-F:]+\]"

def normalize_channel_name(name: str) -> str:
    """根据别名映射表统一频道名称"""
    for standard, aliases in CHANNEL_MAPPING.items():
        if name == standard or name in aliases:
            return standard
    return name

# =============================================
# 新手注意：这里是排除异常线路的区域，可以按需修改
# =============================================

def is_invalid_url(url: str) -> bool:
    """
    检查是否为无效 URL
    在这里添加需要排除的异常线路模式
    """
    # 已知无效或低质量线路模式
    invalid_patterns = [
        # 黑龙江移动某些无效线路
        r"http://\[[a-fA-F0-9:]+\](?::\d+)?/ottrrs\.hl\.chinamobile\.com/.+/.+",
        r"http://\[2409:8087:1a01:df::7005\]/.*",
        
        # 其他已知问题线路可以在这里添加
        # 格式：r"正则表达式模式",
        
        # 示例：排除某些特定的失效域名
        # r".*\.expired-domain\.com.*",
    ]
    
    # 检查是否匹配无效模式
    for pattern in invalid_patterns:
        if re.search(pattern, url):
            return True
    
    return False

def is_preferred_url(url: str) -> bool:
    """
    判断是否为优选线路（适合北方网络环境）
    在这里添加适合北方网络的优质线路模式
    """
    # 优选线路模式（适合北方网络环境的线路）
    preferred_patterns = [
        # 联通线路（北方联通网络质量好）
        r"http://\[2408:.*\]",  # 联通IPv6
        r"http://\d+\.\d+\.\d+\.\d+.*unicom.*",  # 联通IPv4
        
        # 电信线路
        r"http://\[240e:.*\]",  # 电信IPv6
        r"http://\d+\.\d+\.\d+\.\d+.*telecom.*",  # 电信IPv4
        
        # 移动线路
        r"http://\[2409:.*\]",  # 移动IPv6
        r"http://\d+\.\d+\.\d+\.\d+.*mobile.*",  # 移动IPv4
        
        # 北方地区优质线路
        r".*\.bj\.",  # 北京节点
        r".*\.sd\.",  # 山东节点
        r".*\.tj\.",  # 天津节点
        r".*\.heb\.",  # 河北节点
        
        # 其他优质线路特征
        r".*\.cn.*",  # 国内域名
        r".*\.net.*",  # 主流域名
    ]
    
    for pattern in preferred_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

# =============================================
# 核心功能函数区域（一般不需要修改）
# =============================================

def fetch_lines(url: str):
    """下载并分行返回内容"""
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = "utf-8"
        return resp.text.splitlines()
    except Exception as e:
        print(f"❌ 获取失败 {url}: {e}")
        return []

def parse_lines(lines):
    """解析 M3U 或 TXT 内容，返回 {频道名: [url列表]}"""
    channels_dict = defaultdict(list)
    current_name = None

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # M3U #EXTINF 格式
        if line.startswith("#EXTINF"):
            if "," in line:
                current_name = line.split(",")[-1].strip()
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                url = url.split("$")[0].strip()  # 去掉 $ 后缀
                # 检查是否为有效的IPv4或IPv6地址，且不是无效URL
                if (re.match(ipv4_regex, url) or re.match(ipv6_regex, url)) and not is_invalid_url(url):
                    norm_name = normalize_channel_name(current_name)
                    channels_dict[norm_name].append(url)
            current_name = None

        # TXT 频道名,URL 格式
        elif "," in line:
            parts = line.split(",", 1)
            if len(parts) == 2:
                ch_name, url = parts[0].strip(), parts[1].strip()
                url = url.split("$")[0].strip()  # 去掉 $ 后缀
                # 检查是否为有效的IPv4或IPv6地址，且不是无效URL
                if (re.match(ipv4_regex, url) or re.match(ipv6_regex, url)) and not is_invalid_url(url):
                    norm_name = normalize_channel_name(ch_name)
                    channels_dict[norm_name].append(url)

    return channels_dict

def create_m3u_file(all_channels, filename="iptv.m3u"):
    """生成带分类的 M3U 文件，IPv4排在前面，IPv6排在后面"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="https://kakaxi-1.github.io/IPTV/epg.xml"\n\n')
        
        for group, channel_list in CHANNEL_CATEGORIES.items():
            for ch in channel_list:
                if ch in all_channels and all_channels[ch]:
                    # 去重 URL，保留顺序
                    unique_urls = list(dict.fromkeys(all_channels[ch]))
                    
                    # 分离IPv4和IPv6线路
                    ipv4_urls = [url for url in unique_urls if re.match(ipv4_regex, url)]
                    ipv6_urls = [url for url in unique_urls if re.match(ipv6_regex, url)]
                    
                    # 在IPv4和IPv6内部，将优选线路排在前面
                    preferred_ipv4 = [url for url in ipv4_urls if is_preferred_url(url)]
                    other_ipv4 = [url for url in ipv4_urls if not is_preferred_url(url)]
                    
                    preferred_ipv6 = [url for url in ipv6_urls if is_preferred_url(url)]
                    other_ipv6 = [url for url in ipv6_urls if not is_preferred_url(url)]
                    
                    # 最终排序：IPv4优选 -> IPv4其他 -> IPv6优选 -> IPv6其他
                    sorted_urls = preferred_ipv4 + other_ipv4 + preferred_ipv6 + other_ipv6
                    
                    # 写入频道信息
                    logo = f"https://kakaxi-1.github.io/IPTV/LOGO/{ch}.png"
                    f.write(f'#EXTINF:-1 tvg-name="{ch}" tvg-logo="{logo}" group-title="{group}",{ch}\n')
                    
                    # 写入所有URL
                    for url in sorted_urls:
                        f.write(f"{url}\n")

# =============================================
# 新手注意：这里是添加IPTV源的地方，请在这里添加您的稳定源
# =============================================

def main():
    # 在这里添加您的稳定IPTV源URL
    urls = [
        "https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u",  # 示例源1
        # "https://您的第一个稳定源URL",  # 取消注释并替换为您的第一个稳定源
        # "https://您的第二个稳定源URL",  # 取消注释并替换为您的第二个稳定源
        
        # 可以继续添加更多源
        # "https://更多稳定源URL",
    ]

    all_channels = defaultdict(list)

    # 从每个URL获取频道数据
    for url in urls:
        print(f"📡 正在获取: {url}")
        lines = fetch_lines(url)
        parsed = parse_lines(lines)
        for ch, urls_list in parsed.items():
            all_channels[ch].extend(urls_list)
        print(f"✅ 从该源获取到 {len(parsed)} 个频道")

    # 统计信息
    total_channels = len(all_channels)
    total_sources = sum(len(urls) for urls in all_channels.values())
    
    print(f"\n📊 汇总统计:")
    print(f"   总频道数: {total_channels}")
    print(f"   总源数量: {total_sources}")
    
    # 生成最终的M3U文件
    create_m3u_file(all_channels)
    print(f"\n✅ 已生成 iptv.m3u")
    print(f"   文件包含 {total_channels} 个频道，{total_sources} 个播放源")
    print(f"   播放源排序：IPv4优选 → IPv4其他 → IPv6优选 → IPv6其他")

if __name__ == "__main__":
    main()
