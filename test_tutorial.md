---
source_url: "https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101.html"
version: 19.0
last_crawled: "2026-03-01T14:20:04.348912"
title: Server framework 101Â¶
category: developer
headings_structure:
  - Server framework 101Â¶
---

# Server framework 101[Â](<#server-framework-101> "Permalink to this headline")

  * [Chapter 1: Architecture Overview](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/01_architecture.html>)
  * [Chapter 2: A New Application](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/02_newapp.html>)
  * [Chapter 3: Models And Basic Fields](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/03_basicmodel.html>)
  * [Chapter 4: Security - A Brief Introduction](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/04_securityintro.html>)
  * [Chapter 5: Finally, Some UI To Play With](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/05_firstui.html>)
  * [Chapter 6: Basic Views](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/06_basicviews.html>)
  * [Chapter 7: Relations Between Models](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/07_relations.html>)
  * [Chapter 8: Computed Fields And Onchanges](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/08_compute_onchange.html>)
  * [Chapter 9: Ready For Some Action?](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/09_actions.html>)
  * [Chapter 10: Constraints](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/10_constraints.html>)
  * [Chapter 11: Add The Sprinkles](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/11_sprinkles.html>)
  * [Chapter 12: Inheritance](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/12_inheritance.html>)
  * [Chapter 13: Interact With Other Modules](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/13_other_module.html>)
  * [Chapter 14: A Brief History Of QWeb](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/14_qwebintro.html>)
  * [Chapter 15: The final word](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/15_final_word.html>)


Welcome to the Server framework 101 tutorial! If you reached this page that means you are interested in the development of your own Odoo module. It might also mean that you recently joined the Odoo company for a rather technical position. In any case, your journey to the technical side of Odoo starts here.

The goal of this tutorial is for you to get an insight of the most important parts of the Odoo development framework while developing your own Odoo module to manage real estate assets. The chapters should be followed in their given order since they cover the development of a new Odoo application from scratch in an incremental way. In other words, each chapter depends on the previous one.

Important

Before going further, make sure you have prepared your development environment with the [setup guide](<https://www.odoo.com/documentation/19.0/developer/tutorials/setup_guide.html>).

Ready? Letâs get started!

  * [Chapter 1: Architecture Overview](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/01_architecture.html>)

  * [Chapter 2: A New Application](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/02_newapp.html>)

  * [Chapter 3: Models And Basic Fields](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/03_basicmodel.html>)

  * [Chapter 4: Security - A Brief Introduction](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/04_securityintro.html>)

  * [Chapter 5: Finally, Some UI To Play With](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/05_firstui.html>)

  * [Chapter 6: Basic Views](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/06_basicviews.html>)

  * [Chapter 7: Relations Between Models](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/07_relations.html>)

  * [Chapter 8: Computed Fields And Onchanges](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/08_compute_onchange.html>)

  * [Chapter 9: Ready For Some Action?](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/09_actions.html>)

  * [Chapter 10: Constraints](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/10_constraints.html>)

  * [Chapter 11: Add The Sprinkles](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/11_sprinkles.html>)

  * [Chapter 12: Inheritance](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/12_inheritance.html>)

  * [Chapter 13: Interact With Other Modules](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/13_other_module.html>)

  * [Chapter 14: A Brief History Of QWeb](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/14_qwebintro.html>)

  * [Chapter 15: The final word](<https://www.odoo.com/documentation/19.0/developer/tutorials/server_framework_101/15_final_word.html>)


[ **Edit on GitHub](<https://github.com/odoo/documentation/edit/19.0/content/developer/tutorials/server_framework_101.rst>)