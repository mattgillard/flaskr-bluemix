drop table if exists entries;
create table entries (
  id integer primary key auto_increment,
  title text not null,
  text text not null
);
