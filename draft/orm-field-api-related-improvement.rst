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
Historically Django's ORM  has some design limitations and complex internal
API which makes it not only hard to maintain but also produce inconsistant
behaviours.

This type of design limitation made it difficult to add support for
composite primarykey or working with relationField/genericRelations
very annoying as they don't produce consistant behaviour and their
implementaion is hard to maintain due to many special casing.

In order to fix these design limitations and inconsistancies, the proposed
solution is to refactor Fields/RelationFields to new simpler API and
incorporate virtualField type based refctors of RelationFields.


Limitations of ORM that will be taken care of:
==============================================
One limitation is,

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

That way, if we had a new content type (say, a "Post"), it could also 
participate in flagging, without having to modify the model definition 
of "Flag" to add a new foreign key. Without baking in migrations, 
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
the comment from a flag, have to call: 

comment = flag.comment_set.all()[0] 

as the ORM doesn't know for a fact that each flag could only have one 
comment. But Django can implement a OneToManyField in this way 
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


Aim of the Proposal:
====================
This DEP aims to improve django ORM internal Field and related Fields
private api to provide a sane API and mechanism for relation fileds.
Parts of it also propose to introduce true VirtualField type in django. 

To acheive these goals, a better approach would be to Improve Field API,
major cleanup of RealtionField API, model._meta and internal field_valaue_cache
and related areas first.

After completing the major clean ups of Fields/RelationFields a standalone
VirtualField and VirtualField based refactors of ForeignKey and relationFields
and other parts of orm/contenttypes etc could have been done.

This appraoch should keep things easier to approach with smaller steps.

Later any VirtualField derived Field like CompositeField implementation
should be less complex after the completion of virtualField based refactors.

To keep thing sane it would be better to split the Dep in some major Parts:

1. Logical refactor of present Field API and RelationField API, to make 
 them simpler and return consistant result with _meta API calls.

2. Introduce new sane API for RelationFields [internal/provisional]

3. Make it possible to use Reverse relation directly if necessary.

4. Take care of Fields internal value cache for relation fields. [may be] 

5. VirtualField Based refactor of RelationFields API

6. ContentTypes refactor.




Key steps to refactor ORM Fields API internals:
==============================================================
1. Split out Field API logically to separate ConcreteField,
 BaseField, RelationField etc and adjust codes based on that API.

2. Change ForeignObjectRel subclasses to real field instances. 
 The Rel instances are already returned from get_field(), but they
 aren't yet field subclasses. (For example, ForeignKey generates
 a ManyToOneRel in the related model).

3. Allow direct usage of ForeignObjectRel subclasses. In certain cases
 it could be advantageous to be able to define reverse relations directly.
 For example,  ​https://github.com/akaariai/django-reverse-unique.

4. Introduce new standalone well defined ``VirtualField``.

5. Incorporate ``VirtualField`` related changes in django.

6. Refactor ForeignKey based on ``VirtualField`` and ``ConcreteField``
 etc new Field API.

7. Refactor all RelationFields [OneToOne, ManyToMany...] based on ``VirtualField``
 and new Field API based ForeignKey.

8. AuxiliaryField

9. Refactor GenericForeignKey based on ``VirtualField`` based refactored ForeignKey 
 
10. ContentTypes/GenericRelations/GenericForeginKey works well with new Fields API

11. Make changes to migrations framework to work properly with Reafctored Field
   API.

12. Migrations work well with VirtualField based refactored API

13. Make sure new class based Index API ise used properly with refactored Field
   API.

14. Query/QuerySets/Expressions work well with new refactored API's

15. refactor GIS framework based on the changes in ORM

16. ModelForms/Admin work well with posposed changes 



Specifications:
===============

Part-1:
=======

New split out Field API
=========================
1. BaseField:
-------------
Base structure for all Field types in django ORM wheather it is Concrete,
RelationField or VirtualField

2. ConcreteField:
-----------------
ConcreteField will extract all the common attributes of a Regular concrete field

3. Field:
---------
Field class should be refactored using BaseField and ConcreteField. If it
is decided to provide the optional virtual type to regular fields then
VirtualField's features can also be added to specific fields.

4. RelationField:
-----------------
Base Field for All relation fields extended from new BaseField class.
In new class hirerarchy RelationFields will be Virtual.

5. VirtualField:
----------------
A true stand alone VirtualField will be added to solve some long standing
design limitations of django orm. initially RelationFields, GenericRelations
etc will be benefitted by using VirtualFields and later CompositeField or
any virtual type field can be benefitted from VirtualField.



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
        Note that this is different from the target and source fields, which define which
        concrete fields this relation use (essentially, which columns to equate in the
        JOIN condition)
   - The remote field can also contain a descriptor and a manager.
   - For deprecation period, field.rel is a bit like the remote field, but without
     actually being a field instance. This is created only in the origin field,
     the remote field doesn't have a rel (as we don't need backwards compatibility
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
      so the method is called immediately. If the Author model was defined later
      than Book and Book had a string reference to Author, then the method would
      be called only after Author was ready.
 3. The prepare_remote() method is called.
    - The remote field is created based on attributes of the origin field.
    The field is added to the remote model (the field's contribute_to_class
    is called)
    - The post_relation_ready() method is called for both the origin and the remote field.
    This will create the descriptor on both the origin and remote field 
    (unless the remote relation is hidden, in which case no descriptor is created)




Clean up Relation API to make it consistant:
============================================
The problem is that when using get_fields(), you'll get either a
field.rel instance (for reverse side of user defined fields), or
a real field instance(for example ForeignKey). These behave
differently, so that the user must always remember which one
he is dealing with. This creates lots of non-necessary conditioning
in multiple places of Django.

For example, the select_related descent has one branch for descending foreign
keys and one to one fields, and another branch for descending to reverse one
to one fields. Conceptually both one to one and reverse one to one fields
are very similar, so this complication is non-necessary.

The idea is to deprecate field.rel, and instead add field.remote_field.
The remote_field is just a field subclass, just like everything else
in Django.

The benefits are:
Conceptual simplicity - dealing with fields and rels is non-necessaryand confusing.
Everything from get_fields() should be a field.
Code simplicity - no special casing based on if a given relation is described 
by a rel or not
Code reuse - ReverseManyToManyField is in most regard exactly like 
ManyToManyField.

The expected problems are mostly from 3rd party code. Users of _meta that
already work on expectation of getting rel instances will likely need updating.
Those users who subclass Django's fields (or duck-type Django's fields) will
need updating. Examples of such projects include django-rest-framework and
django-taggit.

While the advised approach was:

1. Find places where rield.remote_field responds to different API than Field.
Fix these one at a time while trying to have backwards compat, even if the
API isn't public.

2. In addition, simplifications to the APIs are welcome, as is a high level 
documentation of how related fields actually work.

3. We need to try to keep backwards compat as many projects are forced to
use the private APIs. But most of all, do small incremental changes.


I would like to try the more direct approach. The reasons are,

1. Define clear definition of relation fields class hierarchy and naming
 At present the class names for reverse relation and backreference is
 quite confusing. Like RemoteField is actually holding the information about
 any Fields relation which are now

2. I have plan to introduce OneToManyField which can be used directly
 and will be the main ReverseForeignKey

3. 




Proposed API and workd flow for clean ups:
==========================================
Relational field API
====================
Currently the main use case is that we have a single place where
can be checked that we don't define redundant APIs for related fields.

Structure of a relational field
-------------------------------

A relational field consist of:
 
   - The user created field
   - Possibly of a remote_field, which is auto-created by the user created field
 
 Both the created field and the remote field can possibly add a descriptor to
 the field's model.
 
 Both the remote field and the user created field have (mostly) matching API.
 The API consists of the following attributes and methods:
 
 .. attribute:: name
 
 The name of the field. This is the key of the field in _meta.get_field() calls, and
 thus this is also the name used in ORM queries.
 
 .. attribute:: attr_name
 
 ForeignKeys have the concrete value in field.attr_name, and the model instance in
 field.name. For example Author.book_id contains an integer, and Author.book contains
 a book instance. attr_name is the book_id value.
 
 .. method:: get_query_name()
 
 A method that generates the field's name. Only needed for remote fields.
 
 .. method:: get_accessor_name()
 
 A method that generates the name the field's descriptor should be placed into.
 
 For remote fields, get_query_name() is essentially similar to related_query_name
 parameter, and get_accessor_name() is similar to related_name parameter.
 
 .. method:: get_path_info()
 
 Tells Django which relations to travel when this field is queried. Essentially
 returns one PathInfo structure for each join needed by this field.
 
 .. method:: get_extra_restriction()
 
 Tells Django which extra restrictions should be placed onto joins generated.
 
 .. attribute:: model
 
 The originating model of this field.
 
 .. attribute:: remote_field
 
 The remote field of this model.
 
 .. attribute:: remote_model
 
 Same as self.remote_field.model.
 
 
 Abstract models and relational fields:
  - If an abstract model defines a relation to non-abstract model, we must not add the remote
    field.
  - If an model defines a relation to abstract model, this should just fail (check this!)

This was basically taken from a old work on Relational API clean up, but not well tested.

I believe I can adjust these later.


Part-2:
=======

Introduce standalone ``VirtualField``
=====================================
what is ``VirtualField``?
-------------------------
A VirtualField is a model field type which co-relates to one or multiple
concrete fields, but doesn't add or alter columns in the database.

ORM or migrations certainly can't ignore ForeignKey once it becomes virtual;
instead, migrations will have to hide any auto-generated auxiliary concrete
fields to make migrations backwards-compatible.

A virtualField class could be like the following


class VirtualField(Field):
    """
    Base class for field types with no direct database representation.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('serialize', False)
        kwargs.setdefault('editable', False)
        super().__init__(**kwargs)

    def db_type(self, connection):
        """
        By default no db representation, and thus also no db_type.
        """
        return None

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)

    def get_column(self):
        return None

    @cached_property
    def fields(self):
        return []

    @cached_property
    def concrete_fields(self):
        return [f
                for myfield in self.fields
                for f in myfield.concrete_fields]

    def resolve_concrete_values(self, data):
        if data is None:
            return [None] * len(self.concrete_fields)
        if len(self.concrete_fields) > 1:
            if not isinstance(data, (list, tuple)):
                raise ValueError(
                    "Can't resolve data that isn't list or tuple to values for field %s" %
                    self.name)
            elif len(data) != len(self.concrete_fields):
                raise ValueError(
                    "Invalid amount of values for field %s. Required %s, got %s." %
                    (self.name, len(self.concrete_fields), len(data)))
            return data
        else:
            return [data]




Changes in ``RelationField``
=============================
Relationship fields
~~~~~~~~~~~~~~~~~~~

The fact that related fields are spread across about fifteen different
classes, most of which are quite nontrivial, makes the whole bundle
pretty fragile, which means the changes have to be made carefully not
to break anything. This will require different handling than regular
fields that map directly to database columns.

For that reason the Relational API will be cleaned up to return consistant
result and later VirtualField based refactor will take place.

The first one to look at is ForeignKey since the other two rely on its
functionality, OneToOneField being its descendant and ManyToManyField
using ForeignKeys in the intermediary model. Once the ForeignKeys work,
OneToOneField should require minimal changes since it inherits
almost everything from ForeignKey.


ForeignKey and OneToOneField will also be able to create the underlying
fields automatically when added to the model. I'm proposing the following
default names: "fk_targetname" where "fkname" is the name of the
ForeignKey field and "targetname" is the name of the remote field name
corresponding to the local one. I'm open to other suggestions on this.




Changes in ``ForeignKey``
=========================

Currently ``ForeignKey`` is a regular concrete field which manages both
the raw value stored in the database and the higher-level relationship
semantics. Managing the raw value is simple enough for simple
(single-column) targets. The biggest problem is that many parts of
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
created by its metaclass. 

A better approach could be to add a method such as ``create_auxiliary_copy``
on ``Field`` which would create all new field instances and add them to the
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




``ContentTypes`` and ``GenericForeignKey``
==========================================
Following the refactor of Fields API and introduction of true
VirtualField type, this part will also be refactored.




QuerySet filtering
~~~~~~~~~~~~~~~~~~

The fundamental problem here is that Q objects which are used all over the
code that handles filtering are designed to describe single field lookups.



ModelChoiceFields
~~~~~~~~~~~~~~~~~

As the virtualField itself won't be backed by any real db field

Admin/ModelForms
================



GIS Framework:
==============




