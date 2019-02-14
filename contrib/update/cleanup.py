from os import getenv

from dopy.manager import DoManager


NAME = "serenata-update"


def destroy_droplet(manager):
    droplet_id = None
    for droplet in manager.all_active_droplets():
        if droplet["name"] == NAME:
            droplet_id = droplet["id"]
            break

    if not droplet_id:
        print("Droplet {} not found.".format(NAME))
        return

    output = manager.destroy_droplet(droplet_id)
    print("Droplet {} ({}) deleted.".format(NAME, droplet_id))
    return output


if __name__ == "__main__":
    manager = DoManager(None, getenv("DO_API_TOKEN"), api_version=2)
    destroy_droplet(manager)
