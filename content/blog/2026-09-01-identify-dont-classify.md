---
title: "Identify, Don't Classify: Tagging a Music Library"
date: 2026-09-01
slug: identify-dont-classify
tags: [dj, performance]
draft: false
---

<figure style="margin:0 0 1.8rem;"><img src="/assets/images/blog/identify-dont-classify/hero.png" alt="Identify, Don't Classify: Tagging a Music Library"><figcaption style="font-family:var(--mono);font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;color:var(--text-3);margin-top:8px;">Image: Dyson Hope</figcaption></figure>

I came up agonizing over subgenres. In the mid-90s, I was playing drum & bass, and there was a stretch where I genuinely cared whether a track was techstep or hardstep or darkstep — where I'd sit there and try to decide which bin a record belonged in as if getting it right meant something. It got old within a couple of years. The library kept growing, new subgenres kept crawling out of the woodwork, and every one of them was an argument waiting to happen. At some point, I stepped back and realized I was doing it backwards. I was trying to *classify* my music, and classification is a trap. What I actually needed to do was *identify* it.

That's the whole idea, and everything below is just me working out the consequences of taking it seriously. So let me say the principle plainly before I get into the machinery, because the machinery will date and the principle won't: **describe a song by what it actually is, not by which category you've decided to file it under.** Use adjectives, not nouns. "Identify, don't classify." Once that clicked, a fifteen-year mess of taxonomy turned into something that mostly maintains itself.

## Why classification is a moving target

The problem with subgenres is structural, not a matter of taste. A subgenre can only be defined by a *group* of songs that share characteristics. You cannot listen to a single track in a vacuum and invent the subgenre it belongs to; the category only exists once there's a cluster. Which means the definition is always moving. Every new track that gets called "tech house" subtly bends what tech house means, and a year later the word points at something a little different than it did when you started filing your records under that term. If you're a database person, you already see the issue: you've built your whole organizing model around a moving target. That's a schema that fights you forever.

So I stopped chasing categories and started describing characteristics instead. The distinction sounds small, but it changes everything. It's the difference between a system that needs constant maintenance and one that organizes itself.

When I describe a song, I pick out the things about it that *aren't* subject to trends or shifting opinion — the qualities that are just true about the record whether or not anyone agrees on what to call the style. Is it bright or dark? Flat or dynamic? Is the drum kit tight or loose, big or small — does it have sampled breaks or programmed drums? Are the leads soft or hard? Where does the bass sit — deep sub, midrange, a reese, a hoover, a rumble, or is the bass inseparable from the kick? How much grit is on it: clean, dirty, grinding? What's the tension-release shape: minimal, epic, running, progressive? What are the drum patterns doing — two-step, four-to-the-floor, stripped back? Is there swing, and is it sixteenth or eighth, light or heavy? None of those answers will be relitigated in three years. A dark record stays dark. A loose break stays loose. I'm tagging the *song*, not my current opinion about a genre.

That's the engine. Now here's how it actually lives in the metadata, field by field — and I'll be transparent about this — my system is built for me, one DJ's working system, optimized for one specific use case, not a gospel.

## The use case, because it explains everything else

I'll be clear about who this is for, because the choices only make sense in context. My DJ library and my listening library are two different worlds. In the library I listen to for pleasure, I leave the metadata exactly as the artist intended it — those songs are works of art, and I'm a guest in them. The DJ library is the opposite. Those roughly twenty-five thousand singles are *tools*. They're resources for live performance, and the only thing I'm optimizing for is being able to find the right one fast, in a dark room, mid-set, sometimes when I can't even remember the artist or the title. Compatibility, portability, speed of lookup. Everything that follows is in service of that, and a lot of it would make no sense at all for casual listening.

## Filenames and the artist field: be queryable

First, I clean every filename to one consistent template — artist, title, featured artists, remix and edit names, all in a predictable order. The point isn't tidiness for its own sake; it's that a consistent template lets me run regular expressions across the whole library and trust the results. Inconsistent data can't be operated on at scale. Twenty-five thousand files only stay manageable if they all speak the same grammar.

In the artist field, I'm ruthless about anything that makes a name hard to query. No unusual characters, no strange capitalization, no stray punctuation, no accented foreign characters — anything that would trip up a search or a regex gets normalized out. I'd rather type a clean name and find the record than honor a stylization and lose ten seconds I don't have on stage. When there's more than one artist, I separate them with commas and an ampersand, like plain written English, and I always list them in the *same* order even when a given release lists them differently — consistency beats accuracy-to-the-label every time, because consistency is what makes the field searchable.

One opinion I'll defend: "featuring" clauses belong on the title, not the artist. A guest is featured *on a single song*. The word "featuring" modifies the track, not the act. So a featured vocalist lives in the title field where it belongs, and the artist field stays clean.

## Title and album: credit honestly, identify the dominant voice

The title carries the song name, any featured artists, and any remix or edit name, with the same comma-and-ampersand grammar as the artist field. Two rules here matter more than they look.

First, I credit the *proper* original artist on a remix even when the remixer doesn't bother to. In my library, the track a lot of people know as "Hatiras – Something About You" is filed as "Level 42 – Something About You (Hatiras Remix)," because that's what it actually is. The original artist made the song; the remixer made a version. The metadata should tell the truth about both.

Second — and this is where I do something most people don't — I repurpose the album field entirely. For DJ singles, the album a track originally came from is basically meaningless, and I used to put the record label there until digital releases made label data spotty and unreliable. So now the album field answers a different question: *whose record does this actually sound like?* Dance records are crowded with credits — original artist, features, remixers, editors, mashup makers — and what I care about in the moment is which of those voices dominates. If the track sounds like the remixer's record, the remixer's name goes in the album field. If it sounds more like the original artist — or if I've frankly never heard of the remixer and have nothing else by them — the original artist's name goes there. And when an artist hides behind a dozen aliases — the Eric Prydz / Richie Hawtin / Luke Slater type who releases under whatever name suits the record — I collapse all of it to their single most common identity, so everything they touched lands in one place instead of scattering across half the alphabet. It's a small reassignment of a field nobody was using well, and it turns a dead piece of metadata into a way of grouping by sonic authorship.

You might be wondering why I'm bending the album field into this instead of using a dedicated remixer field — some applications, Serato among them, give you one. The answer is the quiet rule running under this entire system: I only use fields that are part of the actual ID3 standard, the ones every piece of software understands. A remixer field that lives in one program and vanishes the moment I open the library somewhere else isn't an organizing tool, it's a liability — work I'd lose the first time I changed setups. So I'd rather cleverly repurpose a standard field than depend on a non-standard one every time. Cleverness that doesn't travel isn't worth much to someone whose whole library has to survive decades of software coming and going.

## Genre, and the field that does the real work

The genre field stays deliberately dumb. Top-level only — House, Techno, Dubstep, Breakbeat, Drum & Bass, etc. No subgenres. There is no "funky breaks" versus "tech breaks" in my genre field; they're both just Breakbeat. That's not laziness, it's the whole thesis showing up in practice: I refuse to put a moving target in the one field that's supposed to be stable.

The actual intelligence lives in the comments field, and this is the heart of the system. The comment on every track lists its characteristics — those trend-proof adjectives from earlier — alphabetically, comma-delimited. The comma matters because it lets me have multi-word tags. So a record reads as "Dirty, Electro, Vocal," or "16th swing, Atonal, Clean, Glitch, Minimal," or "Minimal, Sub bass, Wobble." And here's the payoff, the thing that makes the whole approach worth the effort: sort the library alphabetically by comment, and songs with similar characteristics fall into clusters on their own, *even across genres*. Subgenres naturally form themselves out of the descriptions, without me ever having to define or maintain one. The categories I refused to classify by come back for free as an emergent property of accurate identification. That's the entire argument of this post compressed into a sort order.

The rest of the fields are quick. BPM I let the software analyze and fill in — no opinion required. Grouping I use for a star rating, specifically because that field survives being pulled out of one application and read by another; a rating I can't carry between programs is a rating I'll lose. Small choice, same principle: portability over cleverness.

## Why this is worth it

Put it together, and a complete record looks like this — clean filename, clean artist, an honest title, an album field pointing at the dominant voice, a top-level genre, and a comment that reads like a description of the actual sound. From there, the comment field runs my entire library. Every tag, every genre, every rating becomes a single-characteristic filter, and I can stack those filters with simple boolean logic to assemble any cross-section I want on demand — every dirty record, every electro record, every house record, and then "dirty electro house" as the intersection of the three, built in seconds, not curated by hand. No more agonizing over whether a song is "bass house" or "future bass house" or whatever.

No single app does all of this in one place, and I've stopped expecting one to — the use cases for music libraries are too diverse for one tool to serve everyone, which is half the reason I never found a turnkey answer and had to build my own logic. The specific applications I lean on will change. They already have (more than once) across the years I've been doing this. What hasn't changed, and won't, is the rule underneath all of it: don't try to file a song into a category that's going to shift under you. Describe what's actually there — the timbre, the grit, the shape, the swing — in words that'll still be true in a decade. Let the categories assemble themselves out of accurate description.

Classify, and you're maintaining a taxonomy forever. Identify, and the library starts organizing itself. That's the difference, and after thirty years of doing this, I'm more sure of it than almost anything else about the work.
