drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  'comment' text not null,
  'tag_id' text not null,
  time_offset text,
  volume integer,
  'item' text not null,
  'type' text not null,
  'playitems' text
);
drop table if exists settings;
create table settings (
   id integer primary key autoincrement,
  'item' text not null,
  'value' text not null,
  'comment' text
);