##>> Test
import os
import sys
sys.path.append(os.getcwd())
from re import compile
##<< Test

## <<Base>>
from random import randint
from time import sleep
from pathlib import Path
from requests import request, exceptions
from urllib.parse import urlparse, parse_qs
from urllib.error import ContentTooShortError
from urllib.request import urlretrieve
from threading import Thread, Lock
from datetime import datetime

## <<Extension>>
import yaml as yml

## <<Third-Part>>

if __name__ == "__main__":
    pass
'''
    # 数据库连接配置
    config = {
        'user': 'your_username',
        'password': 'your_password',
        'host': 'localhost',
        'database': 'social_media_stream_downloader',
        'raise_on_warnings': True
    }

    # 读取 YAML 文件
    with open('Joey乔伊.yml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # 提取数据
    room_data = data['external_info']['data']['room']
    user_data = data['external_info']['data']['user']
    stream_stats = room_data['stats']

    # 插入数据到数据库
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 插入 live_streams 表
        live_stream_query = """
        INSERT INTO live_streams (id, room_id, title, start_time, finish_time, like_count, user_count, stream_url, share_url, create_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        live_stream_values = (
            room_data['id'],
            room_data['room_id'],
            room_data['title'],
            room_data['start_time'],
            room_data['finish_time'],
            room_data['like_count'],
            room_data['user_count'],
            data['summary']['stream_url'],
            data['summary']['share_url'],
            room_data['create_time']
        )
        cursor.execute(live_stream_query, live_stream_values)

        # 插入 users 表
        user_query = """
        INSERT INTO users (id, nickname, sec_uid, gender, signature, verified, follower_count, following_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        user_values = (
            user_data['id'],
            user_data['nickname'],
            user_data['sec_uid'],
            user_data['gender'],
            user_data['signature'],
            user_data['verified'],
            user_data['follow_info']['follower_count'],
            user_data['follow_info']['following_count']
        )
        cursor.execute(user_query, user_values)

        # 插入 admins 表
        for admin_id in room_data['admin_user_ids']:
            admin_query = """
            INSERT INTO admins (user_id, room_id)
            VALUES (%s, %s)
            """
            admin_values = (admin_id, room_data['id'])
            cursor.execute(admin_query, admin_values)

        # 插入 stream_stats 表
        stats_query = """
        INSERT INTO stream_stats (stream_id, comment_count, digg_count, enter_count, follow_count, gift_uv_count)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        stats_values = (
            room_data['id'],
            stream_stats['comment_count'],
            stream_stats['digg_count'],
            stream_stats['enter_count'],
            stream_stats['follow_count'],
            stream_stats['gift_uv_count']
        )
        cursor.execute(stats_query, stats_values)

        conn.commit()
        print("数据插入成功！")

    except Error as e:
        print(f"数据库错误: {e}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("数据库连接已关闭")
'''