[![Build Status](https://img.shields.io/travis/okfn-brasil/serenata-de-amor.svg)](https://travis-ci.org/okfn-brasil/serenata-de-amor)
[![Code Climate](https://img.shields.io/codeclimate/maintainability-percentage/okfn-brasil/serenata-de-amor.svg)](https://codeclimate.com/github/okfn-brasil/serenata-de-amor)
[![Test Coverage](https://img.shields.io/codeclimate/coverage/okfn-brasil/serenata-de-amor.svg)](https://codeclimate.com/github/okfn-brasil/serenata-de-amor/test_coverage)
[![Donate](https://img.shields.io/badge/donate-apoia.se-EB4A3B.svg)](https://apoia.se/serenata)

# [![Operação Serenata de Amor](docs/logo.png)](https://serenata.ai/en)

1. [**Non-tech** crash course into Operação Serenata de Amor](#non-tech-crash-course-into-operação-serenata-de-amor)
2. [**Tech** crash course into Operação Serenata de Amor](#tech-crash-course-into-operação-serenata-de-amor)
3. [Contributing with code and tech skills](#contributing-with-code-and-tech-skills)
4. [Supporting](#supporting)
5. [Acknowledgments](#acknowledgments)

## Non-tech crash course into Operação Serenata de Amor

### What

Serenata de Amor is an open project using artificial intelligence for social control of public administration.

### Who

We are a group of people who believes in _power to the people_ motto. We are also part of the _Data Science for Civic Innovation Programme_ from [Open Knowledge Brasil](http://br.okfn.org).

Among founders and long-term members, we can list a group of eight people – plus numerous contributors from the open source and open knowledge communities:  [Tatiana Balachova](https://tatianasb.ru), [Felipe Cabral](https://twitter.com/felipebcabral), [Eduardo Cuducos](https://cuducos.me),  [Irio Musskopf](https://iriomk.com), [Bruno Pazzim](http://brunopazzim.com/), [Ana Schwendler](http://anaschwendler.com/), [Jessica Temporal](http://jtemporal.com/) and [Pedro Vilanova](https://twitter.com/pedrovilanova).

### How

Similar to organizations like Google, Facebook, and Netflix, we use technology to track government spendings and make open data accessible for everyone. We started looking into data from the Chamber of Deputies (Brazilian lower house) but we expanded to the Federal Senate (Brazilian upper house) and to municipalities.

### When

Irio had the main ideas for the project in early 2016. For a few months, he experimented and gathered people around the project. September, 2016 marks the launching of [our first crowd funding](https://catarse.me/serenata). Since then, we have been creating open source technological products and tools, as well as high quality content on civic tech on our [Facebook](https://fb.com/operacaoserenatadeamor) and [Medium](https://medium.com/serenata).

### Where

We have no non-virtual headquarters, but we work remotely everyday. Most of our ideas are crafted to work in any country that offers open data, but our main implementations focus in Brazil.

### Why

Empowering citizens with data is important: people talk about _smart cities_, _surveillance_ and _privacy_. We prefer to focus on _smart citizens_, _accountability_ and _open knowledge_.

## Tech crash course into Operação Serenata de Amor

### What

Serenata de Amor develops open source tools to make it easy for people to use open data. The focus is to gather relevant insights and share them in an accessible interface. Through this interface, we invite citizens to dialogue with politicians, state and government about public spendings.

### Who

Serenata's main role is played by [Rosie](rosie/README.md): she is an artificial intelligence who analyzes Brazilian congresspeople expenses while they are in office. Rosie can find suspicious spendings and engage citizens in the discussion about these findings. [She's on Twitter](https://twitter.com/RosieDaSerenata).

To allow people to visualize and make sense of data Rosie generates, we have created [Jarbas](jarbas/README.md). On this website, users can browse congresspeople expenses and get details about each of the suspicions. It is the starting point to validate a suspicion.

### How

We have three main repositories [on GitHub](https://github.com/okfn-brasil). This is the _main repo_ and hosts [Rosie](rosie/README.md), [Jarbas](jarbas/README.md) and more experimental code in the `research/` directory.

In addition, we have the [Whistleblower](https://github.com/okfn-brasil/whistleblower) – the tool that gives Rosie the power to tweet – and the [toolbox](https://github.com/okfn-brasil/serenata-toolbox) - a `pip` installable package to follow the [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) principle alongside our repos and modules.

### When

Despite all these players acting together, the core part of the job is ran manually from time to time. The only part that is always online is Jarbas – freely serving a wide range of information about public expenditure 24/7.

Roughly once a month, we manually run Rosie and update Jarbas. A few times per year, we upload versioned datasets accessible via the toolbox – but we encourage you to use the toolbox to generate fresh datasets whenever you need.

### Where

Jarbas is running in [Digital Ocean](https://digitalocean.com) droplets, and deployed using the [Docker Cloud](https://cloud.docker.com/) architecture.

### Why

The answer to most technical _why_ questions is because that is what we had in the past and enabled us to deliver fast. We acknowledge that this is not the best stack ever, but it has brought us here.

## Contributing with code and tech skills

Make sure you have read the _Tech crash course_ on this page. Next, check out our [contributing guide](CONTRIBUTING.md).

## Supporting

* Join our [recurring crowd funding campaign on Apoia.se](http://apoia.se/serenata)
* Donate via Bitcoin to [`1Gbvfjmjvur7qwbwNFdPSNDgx66KSdVB5b`](https://blockchain.info/address/1Gbvfjmjvur7qwbwNFdPSNDgx66KSdVB5b)
* Follow, share and interact with us [on Facebook](https://fb.com/operacaoserenatadeamor)
* Follow, retweet and join [Rosie on Twitter](https://twitter.com/RosieDaSerenata) to interact with your favourite congresspeople

## Acknowledgments

[![Open Knowledge Brasil](docs/okbr.png)](https://br.okfn.org) [![Digital Ocean](docs/digitalocean.png)](https://digitalocean.com)
