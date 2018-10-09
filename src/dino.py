import requests
import configparser
import os
import sqlite3
import click
from dinoserver import add_user


def get_base_url():
    """
    Get base url
    :return: server:port
    """
    dir_name = os.path.dirname(__file__)
    config = configparser.ConfigParser()
    config.read(os.path.join(dir_name, '../config.ini'))
    return config['server']['ip']+":"+config['server']['port']


def get_database():
    """
    Get database object
    :return: database object
    """
    dir_name = os.path.dirname(__file__)
    config = configparser.ConfigParser()
    config.read(os.path.join(dir_name, '../config.ini'))
    return sqlite3.connect(config['database']['db'])


def get_data(url, params=None, method=0):
    """
    get data from a url
    :param url: url
    :param params: parameters
    :param method: 0=GET, 1=POST
    :return: json data, status code
    """
    url = "http://" + url
    r = None
    if method == 0:
        try:
            r = requests.get(url, params)
        except Exception as e:
            return {'error': str(e)}, 400
    elif method == 1:
        try:
            r = requests.post(url, params)
        except Exception as e:
            return {'error': str(e)}, 400
    else:
        return r
    return r.text, r.status_code


def get_users_list():
    """
    :return: get users list
    """
    return get_data(get_base_url())


def remove_user(user_ip):
    """
    Removes a user from the database
    :param user_ip: ip of the user
    :return: message
    """
    db = None
    msg = ""
    users = get_users_list()

    if (user_ip,) not in users:
        msg = "%s: not connected!" % user_ip
        return msg
    try:
        db = get_database()
        cur = db.cursor()
        cur.execute('DELETE FROM USERS WHERE IP = (?)', (user_ip,))
        db.commit()
        msg = "%s: left" % user_ip
    except Exception as e:
        db.rollback()
        msg = "%s: error deleting\n%s" % (user_ip, str(e))
    finally:
        db.close()
        return msg


def check_server():
    """
    Check if the server is up
    :return:
    """
    data, status = get_data(get_base_url())
    if status == 200:
        return True
    return False


@click.group()
def cli():
    """Command line for dino"""
    pass


@cli.command()
def init():
    """Initialize the network and login"""
    """
    Logging in requires the following:
        1. Tell every node that you are here
        2. Update your own host file
        3. Exchange keys with new nodes
    """
    if not check_server():
        click.echo("Dino server is not running currently.")
        click.echo("Start the server and retry.")
        return
    # ping everyone
    for i in range(0, 256):
        my_ip, port = get_base_url().split(":")
        new_url = ".".join(my_ip.split('.')[0:3]) + "." + str(i) + ":" + port
        if new_url == get_base_url():
            continue
        data, status = get_data(new_url+"/join")
        if data:
            click.echo(data)
        if status == 201:
            # active node
            add_user(new_url)


if __name__ == "__main__":
    cli()