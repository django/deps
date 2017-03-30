==============================================================
DEP : ORM Relation Fields API Improvements using VirtualField
==============================================================

:DEP: 0201
:Author: Asif Saif Uddin
:Implementation Team: Asif Saif Uddin, django core team
:Shepherd: Django Core Team
:Status: Draft
:Type: Feature/Cleanup/Optimization
:Created: 2017-3-5
:Last-Modified: 2017-00-00



Background:
===========
Django's ORM is a simple & powerful tool which suits most use-cases.
However, historicaly it has some design limitations and complex internal
API which makes it not only hard to maintain but also produce inconsistant
behaviours.

This type of design limitation made it difficult to add support for
composite primarykey or working with relationField/genericRelations
very annoying as they don't produce consistant behaviour and their
implementaion is hard to maintain due to many special casing.

In order to fix these design limitations and inconsistancies, the proposed
solution is to refactor Fields/RelationFields to new simpler API and
incorporate virtualField type based refctors of RelationFields.


Abstract
==========
This DEP aims to improve different part of django ORM and associated
parts of django to support Real VirtualField type in django. There were
several attempt to fix this problem before. So in this Dep we will try
to follow the suggested approaches from Michal Patrucha's previous works
and suggestions in tickets and IRC chat/mailing list. Few other related
tickets were also analyzed to find out possible way's of API design.


To keep thing sane it would be better to split the Dep in some major Parts:

1. Logical refactor of present Field API and RelationField API, to make 
 them simpler and consistant with _meta API calls

2. Introduce new sane API for RelationFields [internal/provisional]

3. Fields internal value cache refactor for relation fields (may be)

4. VirtualField Based refactor of RelationFields API



Key steps of to follow to improve ORM Field API internals:
==============================================================
1. Split out Field API logically to separate ConcreteField,
 BaseField etc and change on ORM based on the splitted API.

2. Change ForeignObjectRel subclasses to real field instances. (For example,
 ForeignKey generates a ManyToOneRel in the related model). The Rel instances
 are already returned from get_field(), but they aren't yet field subclasses.

3. Allow direct usage of ForeignObjectRel subclasses. In certain cases it
 can be advantageous to be able to define reverse relations directly. For
 example,
 see ​https://github.com/akaariai/django-reverse-unique.

4. Introduce new standalone well defined ``VirtualField``

5. Incorporate ``VirtualField`` related changes in django

6. Refactor ForeignKey based on ``VirtualField`` and ``ConcreteField`` etc NEW Field API

7. Figure out other cases where true virtual fields are needed.

8. Refactor all RelationFields [OneToOne, ManyToMany...] based on ``VirtualField`` and new Field API based ForeignKey

9. Refactor GenericForeignKey based on ``VirtualField`` based refactored ForeignKey 
 
10. Make changes to migrations framework to work properly with Reafctored Field
   API.

11. Migrations work well with VirtualField based refactored API

12. Make sure new class based Index API ise used properly with refactored Field
   API.

13. Query/QuerySets/Expressions work well with new refactored API's

14. ContentTypes/GenericRelations/GenericForeginKey works well with new Fields API



Specifications:
===============

Part-1:
=======

New split out Field API
=========================
1. BaseField:
-------------
Base structure for all Field types in django ORM wheather it is Concrete
or VirtualField

2. ConcreteField:
-----------------
ConcreteField will have all the common attributes of a Regular concrete field

3. Field:
---------
Presence base Field class with should refactored using BaseField and ConcreteField.
If it is decided to provide the optional virtual type to regular fields then VirtualField's features can also be added to specific fields.

4. RelationField:
-----------------

5. VirtualField:
----------------
A true stand alone virtula field will be added to the system to be used to solve some long standing design limitations of django orm. initially RelationFields, GenericRelations etc will be benefitted by using VirtualFields and later CompositeField
or any virtual type field can be benefitted from VirtualField.

Relation Field API clean up:
============================

How relation works in django now:
=================================
Before defining clean up mechanism, lets jump into how relations work in django

A relation in Django consits of:
   - The originating field itself
   - A descriptor to access the objects of the relation
   - The descriptor might need a custom manager
   - Possibly a remote relation field (the field to travel the relation in other direction)
        Note that this is different from the target and source fields, which define which concrete fields this relation use (essentially, which columns to equate in the JOIN condition)
   - The remote field can also contain a descriptor and a manager.
   - For deprecation period, field.rel is a bit like the remote field, but without
     actually being a field instance. This is created only in the origin field, the remote field doesn't have a rel (as we don't need backwards compatibility
     for the remote fields)

 The loading order is as follows:
   - The origin field is created as part of importing the class (or separately
     by migrations).
   - The origin field is added to the origin model's meta (the field's contribute_to_class is called).
   - When both the origin and the remote classes are loaded, the remote field is created and the descriptors are created. The remote field is added to the 
   target class' _meta
   - For migrations it is possible that a model is replaced live in the app-cache. For example,
     assume model Author is changed, and it is thus reloaded. Model Book has foreign key to
     Author, so its reverse field must be recreated in the Author model, too. The way this is
     done is that we collect all fields that have been auto-created as relationships into the
     Author model, and recreate the related field once Author has been reloaded.

 Example:

     class Author(models.Model):
         pass

     class Book(models.Model):
         author = models.ForeignKey(Author)

 1. Author is seen, and thus added to the appconfig.
 2. Book is seen, the field author is seen.
    - The author field is created and assigned to Book's class level variable author.
    - The author field's rel instance is created at the same time the field is created.
    - The metaclass loading for models sees the field instance in Book's attrs,
    and the field is added the class, that is author's contribute_to_class is called.
    - In the contribute_to_class method, the field is added to Book's meta.
    - As last step of contribut_to_class method the prepare_remote() method
      is added as a lazy loaded method. It will be called when both Book and
      Author are ready. As it happens, they are both ready in the example,
      so the method is called immediately.If the Author model was defined later
      than Book, and Book had a string reference to Author, then the method would
      be called only after Author was ready.
 3. The prepare_remote() method is called.
    - The remote field is created based on attributes of the origin field.
    The field is added to the remote model (the field's contribute_to_class
    is called)
    - The post_relation_ready() method is called for both the origin and the remote field. This will create the descriptor on both the origin and remote field 
    (unless the remote relation is hidden, in which case no descriptor is created)

Another limitation is,

Django supports many-to-one relationships -- the foreign keys live on 
the "many", and point to the "one".  So, in a simple app where you 
have Comments that can get Flagged, one Comment can have many Flag's, 
but each Flag refers to one and only one Comment: 

class Comment(models.Model): 
    text = models.TextField() 

class Flag(models.Model): 
    comment = models.ForeignKey(Comment) 

However, there are circumstances where it's much more convenient to 
express the relationship as a one-to-many relationship.  Suppose, for 
example, you want to have a generic "flagging" app which other models 
can use: 

class Comment(models.Model): 
    text = models.TextField() 
    flags = models.OneToMany(Flag) 

That way, if you had a new content type (say, a "Post"), it could also 
participate in flagging, without having to modify the model definition 
of "Flag" to add a new foreign key.  Without baking in migrations, 
there's obviously no way to make the underlying SQL play nice in this 
circumstance: one-to-many relationships with just two tables can only 
be expressed in SQL with a reverse foreign key relationship.  However, 
it's possible to describe OneToMany as a subset of ManyToMany, with a 
uniqueness constraint on the "One" -- we rely on the join table to 
handle the relationship: 

class Comment(models.Model): 
    text = models.TextField() 
    flags = models.ManyToMany(Flag, through=CommentFlag) 

class CommentFlag(models.Model): 
    comment = models.ForeignKey(Comment) 
    flag = models.ForeignKey(Flag, unique=True) 

While this works, the query interface remains cumbersome.  To access 
the comment from a flag, I have to call: 

comment = flag.comment_set.all()[0] 

as the ORM doesn't know for a fact that each flag could only have one 
comment.  But Django _could_ implement a OneToManyField in this way 
(using the underlying ManyToMany paradigm), and provide sugar such 
that this would all be nice and flexible, without having to do cumbersome 
ORM calls or explicitly define extra join tables: 

class Comment(models.Model): 
    text = models.TextField() 
    flags = models.OneToMany(Flag) 

class Post(models.Model): 
    body = models.TextField() 
    flags = models.OneToMany(Flag) 

# in a separate reusable app... 
class Flag(models.Model) 
    reason = models.TextField() 
    resolved = models.BooleanField() 

# in a view... 
comment = flag.comment 
post = flag.post 

It's obviously less database efficient than simple 2-table reverse 
ForeignKey relationships, as you have to do an extra join on the third 
table; but you gain semantic clarity and a nice way to use it in 
reusable apps, so in many circumstances it's worth it. And it's a 
fair shake clearer than the existing generic foreign key solutions.


Clean up Relation API to make it consistant:
============================================
The problem is that when using get_fields(), you'll get either a
field.rel instance (for reverse side of user defined fields), or
a real field instance(for example ForeignKey). These behave
differently, so that the user must always remember which one
he is dealing with. This creates lots of non-necessary conditioning
in multiple places of
Django.

For example, the select_related descent has one branch for descending foreign
keys and one to one fields, and another branch for descending to reverse one
to one fields. Conceptually both one to one and reverse one to one fields
are very similar, so this complication is non-necessary.

The idea is to deprecate field.rel, and instead add field.remote_field.
The remote_field is just a field subclass, just like everything else
in Django.

The benefits are:
Conceptual simplicity - dealing with fields and rels is non-necessaryand confusing. Everything from get_fields() should be a field.
Code simplicity - no special casing based on if a given relation is described 
by a rel or not
Code reuse - ReverseManyToManyField is in most regard exactly like 
ManyToManyField.

The expected problems are mostly from 3rd party code. Users of _meta that
already work on expectation of getting rel instances will likely need updating.
Those users who subclass Django's fields (or duck-type Django's fields) will
need updating. Examples of such projects include django-rest-framework and django-taggit.

Proposed API and workd flow for clean ups:
==========================================





Part-2:
=======

Introduce standalone ``VirtualField``
=====================================
what is ``VirtualField``?
-------------------------
"A virtual field is a model field which it correlates to one or multiple
concrete fields, but doesn't add or alter columns in the database."



Changes in ``ForeignKey``
=========================

Currently ``ForeignKey`` is a regular concrete field which manages both
the raw value stored in the database and the higher-level relationship
semantics. Managing the raw value is simple enough for simple
(single-column) targets. However, in the case of a composite target field,
this task becomes more complex. The biggest problem is that many parts of
the ORM work under the assumption that for each database column there is a
model field it can assign the value from the column to. While it might be
possible to lift this restriction, it would be a really complex project by
itself.

On the other hand, there is the abstraction of virtual fields working on
top of other fields which is required for this project anyway. The way
forward would be to use this abstraction for relationship fields.
Currently, ``ForeignKey`` (and by extension ``OneToOneField``) is the only
field whose ``name`` and ``attname`` differ, where ``name`` stores the
value dictated by the semantics of the field and ``attname`` stores the
raw value from the database.

We can use this to our advantage and put an auxiliary field into the
``attname`` of each ``ForeignKey``, which would be of the same database
type as the target field, and turn ``ForeignKey`` into a virtual field on
top of the auxiliary field. This solution has the advantage that it
offloads the need to manage the raw database value off ``ForeignKey`` and
uses a field specifically intended for the task.

In order to keep this backwards compatible and avoid the need to
explicitly create two fields for each ``ForeignKey``, the auxiliary field
needs to be created automatically during the phase where a model class is
created by its metaclass. Initially I implemented this as a method on
``ForeignKey`` which takes the target field and creates its copy, touches
it up and adds it to the model class. However, this requires performing
special tasks with certain types of fields, such as ``AutoField`` which
needs to be turned into an ``IntegerField`` or ``CompositeField`` which
requires copying its enclosed fields as well.

A better approach is to add a method such as ``create_auxiliary_copy`` on
``Field`` which would create all new field instances and add them to the
appropriate model class.

One possible problem with these changes is that they change the contents
of ``_meta.fields`` in each model out there that contains a relationship
field. For example, if a model contains the following fields::

    ['id',
     'name',
     'address',
     'place_ptr',
     'rating',
     'serves_hot_dogs',
     'serves_pizza',
     'chef']

where ``place_ptr`` is a ``OneToOneField`` and ``chef`` is a
``ForeignKey``, after the change it will contain the following list::

    ['id',
     'name',
     'address',
     'place_ptr',
     'place_ptr_id',
     'rating',
     'serves_hot_dogs',
     'serves_pizza',
     'chef',
     'chef_id']

This causes a lot of failures in the Django test suite, because there are
a lot of tests relying on the contents of ``_meta.fields`` or other
related attributes/properties. (Actually, this example is taken from one
of these tests,
``model_inheritance.tests.ModelInheritanceTests.test_multiple_table``.)
Fixing these is fairly simple, all they need is to add the appropriate
``__id`` fields. However, this raises a concern of how ``_meta`` is
regarded. It has always been a private API officially, but everyone uses
it in their projects anyway. I still think the change is worth it, but it
might be a good idea to include a note about the change in the release
notes. 


Changes in ``RelationField``
=============================
Relationship fields
~~~~~~~~~~~~~~~~~~~

This turns out to be, not too surprisingly, the toughest problem. The fact
that related fields are spread across about fifteen different classes,
most of which are quite nontrivial, makes the whole bundle pretty fragile,
which means the changes have to be made carefully not to break anything.

What we need to achieve is that the ForeignKey, ManyToManyField and
OneToOneField detect when their target field is a CompositeField in
several situations and act accordingly since this will require different
handling than regular fields that map directly to database columns.

The first one to look at is ForeignKey since the other two rely on its
functionality, OneToOneField being its descendant and ManyToManyField
using ForeignKeys in the intermediary model. Once the ForeignKeys work,
OneToOneField should require minimal to no changes since it inherits
almost everything from ForeignKey.

The easiest part is that for composite related fields, the db_type will be
None since the data will be stored elsewhere.

ForeignKey and OneToOneField will also be able to create the underlying
fields automatically when added to the model. I'm proposing the following
default names: "fkname_targetname" where "fkname" is the name of the
ForeignKey field and "targetname" is the name of the remote field name
corresponding to the local one. I'm open to other suggestions on this.

There will also be a way to override the default names using a new field
option "enclosed_fields". This option will expect a tuple of fields each
of whose corresponds to one individual field in the same order as
specified in the target CompositeField. This option will be ignored for
non-composite ForeignKeys.

The trickiest part, however, will be relation traversals in QuerySet
lookups. Currently the code in models.sql.query.Query that creates joins
only joins on single columns. To be able to span a composite relationship
the code that generates joins will have to recognize column tuples and add
a constraint for each pair of corresponding columns with the same aliases
in all conditions.

For the sake of completeness, ForeignKey will also have an extra_filters
method allowing to filter by a related object or its primary key.

With all this infrastructure set up, ManyToMany relationships using
composite fields will be easy enough. Intermediary model creation will
work thanks to automatic underlying field creation for composite fields
and traversal in both directions will be supported by the query code.



``contenttypes`` and ``GenericForeignKey``
==========================================

It's fairly easy to represent composite values as strings. Given an
``escape`` function which uniquely escapes commas, something like the
following works quite well::

    ",".join(escape(value) for value in composite_value)

However, in order to support JOINs generated by ``GenericRelation``, we
need to be able to reproduce exactly the same encoding using an SQL
expression which would be used in the JOIN condition.

Luckily, while thus encoded strings need to be possible to decode in
Python (for example, when retrieving the related object using
``GenericForeignKey`` or when the admin decodes the primary key from URL),
this isn't necessary at the database level. Using SQL we only ever need to
perform this in one direction, that is from a tuple of values into a
string.

That means we can use a generalized version of the function
``django.contrib.admin.utils.quote`` which replaces each unsafe
character with its ASCII value in hexadecimal base, preceded by an escape
character. In this case, only two characters are unsafe -- comma (which is
used to separate the values) and an escape character (which I arbitrarily
chose as '~').

To reproduce this encoding, all values need to be cast to strings and then
for each such string two calls to the ``replace`` functions are made::

    replace(replace(CAST (`column` AS text), '~', '~7E'), ',', '~2C')

According to available documentation, all four supported database backends
provide the ``replace`` function. [2]_ [3]_ [4]_ [5]_

Even though the ``replace`` function seems to be available in all major
database servers (even ones not officially supported by Django, including
MSSQL, DB2, Informix and others), this is still probably best left to the
database backend and will be implemented as
``DatabaseOperations.composite_value_to_text_sql``.

One possible pitfall of this implementation might be that it may not work
with any column type that isn't an integer or a text string due to a
simple fact – the string the database would cast it to will probably
differ from the one Python will use. However, I'm not sure there's
anything we can do about this, especially since the string representation
chosen by the database may be specific for each database server. Therefore
I'm inclined to declare ``GenericRelation`` unsupported for models with a
composite primary key containing any special columns. This should be
extremely rare anyway.


GenericForeignKeys
~~~~~~~~~~~~~~~~~~

Even though the admin uses the contenttypes framework to log the history
of actions, it turns out proper handling on the admin side will make
things work without the need to modify GenericForeignKey code at all. This
is thanks to the fact that the admin uses only the ContentType field and
handles the relations on its own. Making sure the unquoting function
recreates the whole CompositeObjects where necessary should suffice.

At a later stage, however, GenericForeignKeys could also be improved to
support composite primary keys. Using the same quoting solution as in the
admin could work in theory, although it would only allow fields capable of
storing arbitrary strings to be usable for object_id storage. This has
been left out of the scope of this project, though.


QuerySet filtering
~~~~~~~~~~~~~~~~~~

This is where the real fun begins.

The fundamental problem here is that Q objects which are used all over the
code that handles filtering are designed to describe single field lookups.
On the other hand, CompositeFields will require a way to describe several
individual field lookups by a single expression.

Since the Q objects themselves have no idea about fields at all and the
actual field resolution from the filter conditions happens deeper down the
line, inside models.sql.query.Query, this is where we can handle the
filters properly.

There is already some basic machinery inside Query.add_filter and
Query.setup_joins that is in use by GenericRelations, this is
unfortunately not enough. The optional extra_filters field method will be
of great use here, though it will have to be extended.

Currently the only parameters it gets are the list of joins the
filter traverses, the position in the list and a negate parameter
specifying whether the filter is negated. The GenericRelation instance can
determine the value of the content type (which is what the extra_filters
method is used for) easily based on the model it belongs to.

This is not the case for a CompositeField -- it doesn't have any idea
about the values used in the query. Therefore a new parameter has to be
added to the method so that the CompositeField can construct all the
actual filters from the iterable containing the values.

Afterwards the handling inside Query is pretty straightforward. For
CompositeFields (and virtual fields in general) there is no value to be
used in the where node, the extra_filters are responsible for all
filtering, but since the filter should apply to a single object even after
join traversals, the aliases will be set up while handling the "root"
filter and then reused for each one of the extra_filters.

This way of extending the extra_filters mechanism will allow the field
class to create conjunctions of atomic conditions. This is sufficient for
the "__exact" lookup type which will be implemented.

Of the other lookup types, the only one that looks reasonable is "__in".
This will, however, have to be represented as a disjunction of multiple
"__exact" conditions since not all database backends support tuple
construction inside expressions. Therefore this lookup type will be left
out of this project as the mechanism would need much more work to make it
possible.


``__in`` lookups for ``VirtualField``
=======================================

The existing implementation of ``CompositeField`` handles ``__in`` lookups
in the generic, backend-independent ``WhereNode`` class and uses a
disjunctive normal form expression as in the following example::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE (a = 1 AND b = 2 AND c = 3) OR (a = 4 AND b = 5 AND c = 6);

The problem with this solution is that in cases where the list of values
contains tens or hundreds of tuples, this DNF expression will be extremely
long and the database will have to evaluate it for each and every row,
without a possibility of optimizing the query.

Certain database backends support the following alternative::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE (a, b, c) IN [(1, 2, 3), (4, 5, 6)];

This would probably be the best option, but it can't be used by SQLite,
for instance. This is also the reason why the DNF expression was
implemented in the first place.

In order to support this more natural syntax, the ``DatabaseOperations``
needs to be extended with a method such as ``composite_in_sql``.

However, this leaves the issue of the inefficient DNF unresolved for
backends without support for tuple literals. For such backends, the
following expression is proposed::

    SELECT a, b, c FROM tbl1, tbl2
    WHERE EXISTS (SELECT a1, b1, c1, FROM (SELECT 1 as a, 2 as b, 3 as c
                                           UNION SELECT 4, 5, 6)
                  WHERE a1=1 AND b1=b AND c1=c);

Since both syntaxes are rather generic and at least one of them should fit
any database backend directly, a new flag will be introduced,
``DatabaseFeatures.supports_tuple_literals`` which the default
implementation of ``composite_in_sql`` will consult in order to choose
between the two options.

ModelChoiceFields
~~~~~~~~~~~~~~~~~

Again, we need a way to specify the value as a parameter passed in the
form. The same escaping solution can be used even here.

Admin/ModelForms
================

The solution that has been proposed so many times in the past [2], [3] is
to extend the quote function used in the admin to also quote the comma and
then use an unquoted comma as the separator. Even though this solution
looks ugly to some, I don't think there is much choice -- there needs to
be a way to separate the values and in theory, any character could be
contained inside a value so we can't really avoid choosing one and
escaping it.


Other considerations
--------------------

Notes on Porting previous work on top of master:
================================================
Considering the huge changes in ORM internals it is neither practical nor
trivial to rebase & port previous works related to ForeignKey refactor and CompositeKey without figuring out new approach based on present ORM internals
design on top of master.

A better approach would be to Improve Field API, major cleanup of RealtionField
API, model._meta and internal field_valaue_cache and related areas first.

After completing the major clean ups of Fields/RelationFields a REAL
VirtualField type should be introduced and VirtualField based refactor
of ForeignKey and relationFields could done.

This appraoch should keep things sane and easier to approach on smaller chunks.

Later any VirtualField derived Field like CompositeField implementation
should be less complex after the completion of virtualField based refactors.
