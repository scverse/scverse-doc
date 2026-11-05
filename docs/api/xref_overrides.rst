``scverse_doc.xref_overrides``
==============================

.. automodule:: scverse_doc.xref_overrides
   :members: DEFAULT_OVERRIDES

Examples
--------

:class:`~concurrent.futures.ThreadPoolExecutor` is defined in ``concurrent.futures.thread``,
so `conf.py` has

.. code:: python

   xref_overrides = {"concurrent.futures.thread.ThreadPoolExecutor": "concurrent.futures.ThreadPoolExecutor"}

With that, and with ``ThreadPoolExecutor`` imported in an ``if TYPE_CHECKING:`` block,
the annotation of

.. literalinclude:: ../examples.py
   :pyobject: run

links to its documentation:

.. autofunction:: examples.run
