
.. image:: _static/images/title.png
   :alt: [logo]
   :align: center
   :width: 500px

lala
=========



 lala is a Python library to plan and analyze primer-based verification of DNA assemblies, using Sanger sequencing or verification PCR. It implements methods to design and select primers to ensure that the relevant assembly segments will be covered, and it

 Usage
 -----

 **Primer selection**

 The following code assumes that a file ``available_primers.fa`` contains the labels and sequences of all available primers in the lab, and that the assemblies to be sequence-verified have annotations indicating the zones that the sequencing should cover and zones where primer annealing should be avoided.

 .. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/docs/_static/images/annotated_genbank.png
    :width: 600px

 .. code:: python

     from lala import PrimerSelector, Primer, load_record
     import os

     # LOAD ASSEMBLIES RECORDS AND AVAILABLE PRIMERS
     records = [load_record(file_path, linear=False)
                for file_path in ['my_record_1.gb', 'my_record_2.gb'...]]
     available_primers = Primer.list_from_fasta("example_primers.fa")

     # SELECT THE BEST PRIMERS
     selector = PrimerSelector(tm_range=(55, 70), size_range=(16, 25))
     selected_primers = selector.select_primers(records, available_primers)

     # PLOT THE COVERAGE AND WRITE THE PRIMERS IN A SPREADSHEET
     selector.plot_coverage(records, selected_primers, 'coverage.pdf')
     selector.write_primers_table(selected_primers, 'selected_primers.csv')

 The returned ``selected_primers`` contains a list of lists of primers (one list for each construct). The PDF report returned looks like this:

 .. image:: https://raw.githubusercontent.com/Edinburgh-Genome-Foundry/lala/master/docs/_static/images/annotated_primer_selection.png
    :width: 600px

 **Sequencing Validation**

 (documentation for this feature is coming soon)


Installation
-------------

You can install lala through PIP

.. code::

    sudo pip install lala

Alternatively, you can unzip the sources in a folder and type

.. code::

    sudo python setup.py install

To be able to generate plots and reports, run

.. code::

    sudo pip install dna_features_viewer weasyprint

License = MIT
--------------

lala is an open-source software originally written at the `Edinburgh Genome Foundry
<http://edinburgh-genome-foundry.github.io/home.html>`_ by `Zulko <https://github.com/Zulko>`_
and `released on Github <https://github.com/Edinburgh-Genome-Foundry/lala>`_ under the MIT licence (¢ Edinburg Genome Foundry).

Everyone is welcome to contribute !


.. raw:: html

       <a href="https://twitter.com/share" class="twitter-share-button"
       data-text="lala - A Python module for automatic primer selection and sequencing validation" data-size="large" data-hashtags="Bioprinting">Tweet
       </a>
       <script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';
       if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+'://platform.twitter.com/widgets.js';
       fjs.parentNode.insertBefore(js,fjs);}}(document, 'script', 'twitter-wjs');
       </script>
       <iframe src="http://ghbtns.com/github-btn.html?user=Edinburgh-Genome-Foundry&repo=lala&type=watch&count=true&size=large"
       allowtransparency="true" frameborder="0" scrolling="0" width="152px" height="30px" margin-bottom="30px"></iframe>




.. toctree::
    :hidden:
    :maxdepth: 3

    self

.. toctree::
   :hidden:
   :caption: Reference
   :maxdepth: 3

   ref/ref

.. toctree::
   :caption: Examples

   examples/primer_selection_example

.. _PYPI: https://pypi.python.org/pypi/lala
