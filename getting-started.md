# Climb Log — Getting Started

This guide explains how to create your own version of Climb Log, maintain your own gym list, and receive updates to the application.

You don't need to install anything or use the command line. Everything can be done through the GitHub website.

---

## 1. First-time setup

### Create a GitHub account

If you don't already have one, go to:

**https://github.com/**

Click **Sign up** and follow the instructions.

One note: the user name you will pick will be part of the url hosting your version: https://github.com/YOUR-USERNAME/gym

---

### Fork the Climb Log repository

Open:

**https://github.com/stefanvr/gym**

Make sure you are logged in, then click **Fork**.

Choose your own GitHub account as the destination.

You now have your own copy of Climb Log.

It will have an address similar to:

```text
https://github.com/YOUR-USERNAME/gym
```

---

### Turn on your website

* Click Settings.
* In the left-hand menu, find Pages.
* Under Build and deployment, find Source.
* Select GitHub Actions.

### Tell Climb Log to use your gym collection

Your fork contains two gym folders:

- `gyms/` — Stefan's gym collection
- `gyms-my/` — your gym collection

The application needs to know which one to use.

In your repository, open the file:

```text
.gymrc
```

This file is in the **root** of the repository.

Click the **✏️ pencil icon** to edit it.

Change the gym folder to:

```text
gyms-my
```

Then click **Commit changes**.

**This is the only setup change you need to make.**

---

### Your website

Your Climb Log website is normally available at:

```text
https://YOUR-USERNAME.github.io/gym/
```

It may take a few minutes for the first build to finish.

If the change doesn't appear immediately, don't panic. Open the Actions tab in your GitHub repository. You should see a workflow running or completed. If it has a green check mark, the build succeeded.

If the build is red: Let me know and I'll help you resolve it.
---

# 2. Maintaining your gyms

From now on, your main workspace is:

```text
gyms-my/
```

You can use the files in `gyms/` as examples, but **only maintain your own gyms in `gyms-my/`**.

### Edit an existing gym

1. Open `gyms-my/`.
2. Click the gym you want to change.
3. Click the **✏️ pencil icon**.
4. Make your changes.
5. Click **Commit changes**.

### Add a new gym

1. Open `gyms-my/`.
2. Click **Add file → Create new file**.
3. Give the file a name, for example:
   `nl-ivy-climbing-sittard.md`
4. Use an existing gym file as an example/template.
5. Enter the information for the new gym.
6. Click **Commit changes**.

The existing gym files show you the required format, so you don't need to learn or remember it separately.

### After making changes

GitHub automatically builds the website.

It can take a few minutes before your changes appear on the website. see "Your website" for more info.

---

# 3. Getting updates to the application

I will occasionally publish updates to Climb Log, such as new features, improvements or bug fixes.

You can update your copy without replacing your own gym collection.

Open your GitHub repository and look for the **Sync fork** button.

Click:

**Sync fork → Update branch**

This brings the latest application changes from the original repository into your fork.

Your own gyms remain in:

```text
gyms-my/
```

### If GitHub reports a conflict

Don't try to fix it yourself.

Let me know and I'll help you resolve it.

---

## In short

After the one-time setup, there are only two things you need to remember:

**To maintain your gyms:**

`GitHub → your repository → gyms-my/`

**To get application updates:**

`GitHub → your repository → Sync fork → Update branch`

That's it. 🧗