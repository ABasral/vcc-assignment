# -*- mode: ruby -*-
# vi: set ft=ruby :
# ============================================================
# VCC Assignment 3 - Vagrantfile for Local VM Setup
# Creates an Ubuntu VM with all dependencies pre-installed
# ============================================================

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "vcc-local-vm"

  # Forward Flask app port
  config.vm.network "forwarded_port", guest: 5000, host: 5050

  # VM resources
  config.vm.provider "virtualbox" do |vb|
    vb.name = "VCC-Assignment3-LocalVM"
    vb.memory = "2048"
    vb.cpus = 2
  end

  # Sync project files into the VM
  config.vm.synced_folder ".", "/home/vagrant/app"

  # Provisioning script
  config.vm.provision "shell", inline: <<-SHELL
    set -e

    echo "=== Setting up VCC Assignment 3 VM ==="

    # Update and install dependencies
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv curl stress-ng

    # Setup Python environment
    cd /home/vagrant/app
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Install Google Cloud SDK
    if ! command -v gcloud &> /dev/null; then
      echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
        tee /etc/apt/sources.list.d/google-cloud-sdk.list
      curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
        apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
      apt-get update -y
      apt-get install -y google-cloud-cli
    fi

    echo "=== VM Setup Complete ==="
    echo "Run: cd /home/vagrant/app && source venv/bin/activate"
    echo "Then: python src/app.py"
  SHELL
end
