from os import getenv

from dopy.manager import DoManager


NAME = "serenata-update"


def get_id(objects):
    for object in objects:
        if object["name"] == NAME:
            return object["id"]


def destroy_droplet(manager):
    droplet = get_id(manager.all_active_droplets())
    if not droplet:
        print "Droplet {} not found.".format(NAME)
        return

    output = manager.destroy_droplet(droplet)
    print "Droplet {} ({}) deleted.".format(NAME, droplet)
    return output


def destroy_ssh_key(manager):
    ssh_key = get_id(manager.all_ssh_keys())
    if not ssh_key:
        print "SSH key {} not found.".format()
        return

    output = manager.destroy_ssh_key(ssh_key)
    print "SSH key {} ({}) deleted.".format(NAME, ssh_key)
    return output


if __name__ == "__main__":
    manager = DoManager(None, getenv("DO_API_TOKEN"), api_version=2)
    destroy_droplet(manager)
    destroy_ssh_key(manager)
