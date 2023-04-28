from os import link
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.firefox.options import Options
from discord import Webhook, RequestsWebhookAdapter, Embed
from json import load, dump
from sys import exit
from time import sleep
import datetime

with open("creds.json", "r") as f:
    creds = load(f)

with open("logs.json", "r") as f:
    old_logs = load(f)

options = Options()
message_sent = False
# options.binary_location = r'/usr/bin/firefox' # When using crontab it may need firefox in a specific location. Comment this life if you are using this on windows.
options.headless = False  # Since most of people are gonna use it on windows. you should see the process. if you don't to make this headless
driver = webdriver.Firefox(options=options)


""" # Disable this comment if you want it to complete action quickly (not recommended)
def sleep(time:int):
    pass
"""
initial_stuff = creds["creds"][0]

todays_date_obj = datetime.datetime.now().date()
todays_date = todays_date_obj.strftime("%Y,%m,%d")

webhook = Webhook.from_url(
    initial_stuff["webhook_url"], adapter=RequestsWebhookAdapter()
)
embed = Embed(color=0xFF00FF, title=f"Script was runned")
webhook.send(embed=embed)

for credss in creds["creds"]:
    username = credss["username"]
    password = credss["password"]
    base_link = credss["base_link"]
    content = credss["content"]
    webhook_url = credss["webhook_url"]

    driver.get(f"{base_link}/login/index.php")
    usr_entry = driver.find_element_by_id("username")
    pass_entry = driver.find_element_by_id("password")
    loginbtn = driver.find_element_by_id("loginbtn")

    usr_entry.send_keys(username)
    pass_entry.send_keys(password)
    loginbtn.click()
    sleep(5)

    driver.get(f"{base_link}/calendar/view.php?view=day")
    sleep(5)

    links = []
    for event in driver.find_elements_by_class_name("card-link"):
        l = event.get_attribute("href")
        if (
            "attendance" in l
        ):  # Only care about link in which we have to give attendance
            links.append(l)

    for link in links:
        driver.get(link)
        sleep(5)
        class_name = driver.find_element_by_class_name("page-header-headings").text
        log_to_pass = {"id": username, "date": todays_date, "class": class_name}
        if log_to_pass in old_logs["logs"]:
            continue
        if not message_sent:
            webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())
            embed = Embed(
                color=0x0000FF, title=f"Bot Was runned and found some classes."
            )
            embed.add_field(name="For", value=username)
            webhook.send(content=content, embed=embed)
            message_sent = True

        try:
            submit_btn = driver.find_element_by_xpath(
                "// a[contains(text(),'Submit attendance')]"
            )
        except exceptions.NoSuchElementException:
            webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())
            embed = Embed(color=0xFF0000, title="Failed, No Button Present.")
            embed.add_field(name="Class Name", value=class_name)
            embed.add_field(name="Student ID", value=username)
            webhook.send(embed=embed)
            # old_logs["logs"].append(log_to_pass) # Don't push if it fails to get one. in future may get one.
            continue

        submit_btn.click()
        driver.find_elements_by_class_name("form-check-input")[0].click()
        sleep(1)
        driver.find_element_by_id("id_submitbutton").click()
        sleep(1)
        sleep(1)
        sleep(1)
        webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())
        embed = Embed(color=0x00FF00, title="Success")
        embed.add_field(name="Class Name", value=class_name)
        embed.add_field(name="Student ID", value=username)
        webhook.send(embed=embed)
        old_logs["logs"].append(log_to_pass)
    # Log out now to move on to another account
    driver.get(f"{base_link}/login/logout.php")
    driver.find_element_by_class_name("btn-primary").click()
    message_sent = False


with open("logs.json", "w+") as f:
    dump(old_logs, f, indent=4)

driver.close()  # Why not save some memory?
