# -*- coding: utf-8 -*-
from .objective import Objective
from .variable import Variable
from .constraint import Constraint
from .data import Set, Parameter
from .dataframe import DataFrame
from .iterators import MapEntities
from . import amplpython


class AMPL:
    """An AMPL translator.

    An object of this class can be used to do the following tasks:

    - Run AMPL code. See :func:`~amplpy.AMPL.eval` and
      :func:`~amplpy.AMPL.evalAsync`.
    - Read models and data from files. See :func:`~amplpy.AMPL.read`,
      :func:`~amplpy.AMPL.readData`, :func:`~amplpy.AMPL.readAsync`, and
      :func:`~amplpy.AMPL.readDataAsync`.
    - Solve optimization problems constructed from model and data (see
      :func:`~amplpy.AMPL.solve` and :func:`~amplpy.AMPL.solveAsync`).
    - Access single Elements of an optimization problem. See
      :func:`~amplpy.AMPL.getVariable`, :func:`~amplpy.AMPL.getConstraint`,
      :func:`~amplpy.AMPL.getObjective`, :func:`~amplpy.AMPL.getSet`,
      and :func:`~amplpy.AMPL.getParameter`.
    - Access lists of available entities of an optimization problem. See
      :func:`~amplpy.AMPL.getVariables`, :func:`~amplpy.AMPL.getConstraints`,
      :func:`~amplpy.AMPL.getObjectives`, :func:`~amplpy.AMPL.getSets`,
      and :func:`~amplpy.AMPL.getParameters`.

    Error handling is two-faced:

    - Errors coming from the underlying AMPL translator (e.g. syntax errors and
      warnings obtained calling the eval method) are handled by
      the :class:`~amplpy.ErrorHandler` which can be set and get via
      :func:`~amplpy.AMPL.getErrorHandler` and
      :func:`~amplpy.AMPL.setErrorHandler`.
    - Generic errors coming from misusing the API, which are detected in
      Python, are thrown as exceptions.

    The default implementation of the error handler throws exceptions on errors
    and prints to console on warnings.

    The output of every user interaction with the underlying translator is
    handled implementing the abstract class :class:`~amplpy.OutputHandler`.
    The (only) method is called at each block of output from the translator.
    The current output handler can be accessed and set via
    :func:`~amplpy.AMPL.getOutputHandler` and
    :func:`~amplpy.AMPL.setOutputHandler`.
    """

    def __init__(self, environment=None):
        """
        Constructor:
        creates a new AMPL instance with the specified environment if provided.

        Args:
            environment (:class:`~amplpy.Environment`): This allows the user to
            specify the location of the AMPL binaries to be used and to modify
            the environment variables in which the AMPL interpreter will run.

        Raises:
            RunTimeError: If no valid AMPL license has been found or if the
            translator cannot be started for any other reason.
        """
        if environment is None:
            self._impl = amplpython.AMPL()
        else:
            self._impl = amplpython.AMPL(environment._impl)
        self._outputhandler = None
        self._errorhandler = None

    def __del__(self):
        """
        Default destructor:
        releases all the resources related to the AMPL instance (most notably
        kills the underlying  interpreter).
        """
        self.close()

    def getData(self, *statements):
        """
        Get the data corresponding to the display statements. The statements
        can be AMPL expressions, or entities. It captures the equivalent of the
        command:

        .. code-block:: ampl

            display ds1, ..., dsn;

        where ds1, ..., dsn are the ``displayStatements`` with which the
        function is called.

        As only one DataFrame is returned, the operation will fail if the
        results of the display statements cannot be indexed over the same set.
        As a result, any attempt to get data from more than one set, or to get
        data for multiple parameters with a different number of indexing sets
        will fail.

        Args:
            statements: The display statements to be fetched.

        Raises:
            AMPLException: if the AMPL visualization command does not succeed
            for one of the reasons listed above.

        Returns:
            DataFrame capturing the output of the display
            command in tabular form.
        """
        return DataFrame.fromDataFrameRef(
            self._impl.getData(list(statements), len(statements))
        )

    def getEntity(self, name):
        """
        Get entity corresponding to the specified name (looks for it in all
        types of entities).

        Args:
            name: Name of the entity.

        Raises:
            OutOfRangeException: if the specified entity does not exist.

        Returns:
            The AMPL entity with the specified name.
        """
        raise NotImplementedError  # TODO

    def getVariable(self, name):
        """
        Get the variable with the corresponding name.

        Args:
            name: Name of the variable to be found.

        Raises:
            OutOfRangeException: if the specified variable does not exist.
        """
        return Variable(self._impl.getVariable(name))

    def getConstraint(self, name):
        """
        Get the constraint with the corresponding name.

        Args:
            name: Name of the constraint to be found.

        Raises:
            OutOfRangeException: if the specified constraint does not exist.
        """
        return Constraint(self._impl.getConstraint(name))

    def getObjective(self, name):
        """
         Get the objective with the corresponding name.

         Args:
            name: Name of the objective to be found.

        Raises:
            OutOfRangeException: if the specified objective does not exist.
        """
        return Objective(self._impl.getObjective(name))

    def getSet(self, name):
        """
        Get the set with the corresponding name.

        Args:
            name: Name of the set to be found.

        Raises:
            OutOfRangeException: if the specified set does not exist.
        """
        return Set.fromSetRef(self._impl.getSet(name))

    def getParameter(self, name):
        """
        Get the parameter with the corresponding name.

        Args:
            name: Name of the parameter to be found.

        Raises:
            OutOfRangeException: if the specified parameter does not exist.
        """
        return Parameter.fromParameterRef(self._impl.getParameter(name))

    def eval(self, amplstatements):
        """
        Parses AMPL code and evaluates it as a possibly empty sequence of AMPL
        declarations and statements.

        As a side effect, it invalidates all entities (as the passed statements
        can contain any arbitrary command); the lists of entities will be
        re-populated lazily (at first access)

        The output of interpreting the statements is passed to the current
        OutputHandler (see getOutputHandler and
        setOutputHandler).

        By default, errors are reported as exceptions and warnings are printed
        on stdout. This behavior can be changed reassigning an ErrorHandler
        using setErrorHandler.

        Args:
          amplstatements: A collection of AMPL statements and declarations to
          be passed to the interpreter.

        Raises:
          RunTimeError: if the input is not a complete AMPL statement (e.g.
          if it does not end with semicolon) or if the underlying
          interpreter is not running.
        """
        self._impl.eval(amplstatements)

    def reset(self):
        """
        Clears all entities in the underlying AMPL interpreter, clears all maps
        and invalidates all entities.
        """
        self.eval("reset;")
        # self._impl.reset()  # FIXME: causes Segmentation fault

    def close(self):
        """
        Stops the underlying engine, and release all any further attempt to
        execute optimization commands without restarting it will throw an
        exception.
        """
        self._impl.close()

    def isRunning(self):
        """
        Returns true if the underlying engine is running.
        """
        self._impl.isRunning()

    def isBusy(self):
        """
        Returns true if the underlying engine is doing an async operation.
        """
        self._impl.isBusy()

    def solve(self):
        """
        Solve the current model.

        Raises:
            RunTimeError: if the underlying interpreter is not running.
        """
        self._impl.solve()

    def readAsync(self, filename, callback):
        """
        Interprets the specified file asynchronously, interpreting it as a
        model or a script file. As a side effect, it invalidates all entities
        (as the passed file can contain any arbitrary command); the lists of
        entities will be re-populated lazily (at first access).

        Args:
            filename: Path to the file (Relative to the current working
            directory or absolute).

            callback: Callback to be executed when the file has been
            interpreted.
        """
        raise NotImplementedError

    def readDataAsync(self, filename, callback):
        """
        Interprets the specified data file asynchronously. When interpreting is
        over, the specified callback is called. The file is interpreted as
        data. As a side effect, it invalidates all entities (as the passed file
        can contain any arbitrary command); the lists of entities will be
        re-populated lazily (at first access)

        Args:
            filename: Full path to the file.

            callback: Callback to be executed when the file has been
            interpreted.
        """
        raise NotImplementedError

    def evalAsync(self, amplstatements, callback):
        """
        Interpret the given AMPL statement asynchronously.

        Args:
          amplstatements: A collection of AMPL statements and declarations to
          be passed to the interpreter.

          callback: Callback to be executed when the statement has been
          interpreted.

        Raises:
          RunTimeError: if the input is not a complete AMPL statement (e.g.
          if it does not end with semicolon) or if the underlying
          interpreter is not running.
        """
        raise NotImplementedError

    def solveAsync(self, callback):
        """
        Solve the current model asynchronously.

        Args:
          callback: Callback to be executed when the solver is done.
        """
        raise NotImplementedError

    def interrupt(self):
        """
        Interrupt an underlying asynchronous operation (execution of AMPL code
        by the AMPL interpreter). An asynchronous operation can be started via
        evalAsync(), solveAsync(), readAsync() and readDataAsync().
        Does nothing if the engine and the solver are idle.
        """
        raise NotImplementedError

    def cd(self, path=None):
        """
        Get or set the current working directory from the underlying
        interpreter (see https://en.wikipedia.org/wiki/Working_directory).

        Args:
            path: New working directory or None (to display the working
            directory).

        Returns:
            Current working directory.
        """
        if path is None:
            return self._impl.cd()
        else:
            return self._impl.cd(path)

    def setOption(self, name, value):
        """
        Set an AMPL option to a specified value.

        Args:
            name: Name of the option to be set (alphanumeric without spaces).

            value: The value the option must be set to.

        Raises:
            InvalidArgumet: if the option name is not valid.

            TypeError: if the value has an invalid type.
        """
        if isinstance(value, int):
            return self._impl.setIntOption(name, value)
        elif isinstance(value, float):
            return self._impl.setIntOption(name, value)
        elif isinstance(value, bool):
            return self._impl.setBoolOption(name, value)
        elif isinstance(value, basestring):
            return self._impl.setOption(name, value)
        else:
            raise TypeError

    def getOption(self, name):
        """
         Get the current value of the specified option. If the option does not
         exist, returns None.

         Args:
            name: Option name.

        Returns:
            Value of the option.

        Raises:
            InvalidArgumet: if the option name is not valid.
        """
        try:
            value = self._impl.getOption(name).value()
        except RuntimeError:
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def read(self, fileName):
        """
        Interprets the specified file (script or model or mixed) As a side
        effect, it invalidates all entities (as the passed file can contain any
        arbitrary command); the lists of entities will be re-populated lazily
        (at first access).

        Args:
            fileName: Full path to the file.

        Raises:
            RunTimeError: in case the file does not exist.
        """
        self._impl.read(fileName)

    def readData(self, fileName):
        """
        Interprets the specified file as an AMPL data file. As a side effect,
        it invalidates all entities (as the passed file can contain any
        arbitrary command); the lists of entities will be re-populated lazily
        (at first access). After reading the file, the interpreter is put back
        to "model" mode.

        Args:
            fileName: Full path to the file.

        Raises:
            RunTimeError: in case the file does not exist.
        """
        self._impl.readData(fileName)

    def getValue(self, scalarExpression):
        """
        Get a scalar value from the underlying AMPL interpreter, as a double or
        a string.

        Args:
            scalarExpression: An AMPL expression which evaluates to a scalar
            value.

        Returns:
            The value of the expression.
        """
        return self._impl.getValue(scalarExpression)

    def setData(self, dataframe):
        """
        Assign the data in the dataframe to the AMPL entities with the names
        corresponding to the column names.

        Args:
            dataFrame: The dataframe containing the data to be assigned.

        Raises:
            AMPLException: if the data assignment procedure was not successful.
        """
        self._impl.setData(dataframe._impl)

    def display(self, *amplExpressions):
        """
        Writes on the current OutputHandler the outcome of the AMPL statement.

        .. code-block:: ampl

            display e1, e2, .., en;

        where e1, ..., en are the strings passed to the procedure.

        Args:
            amplExpressions: Expressions to be evaluated.
        """
        raise NotImplementedError

    def setOutputHandler(self, outputhandler):
        """
        Sets a new output handler.

        Args:
            outputhandler: The function handling the AMPL output derived from
            interpreting user commands.
        """
        self._outputhandler = outputhandler
        self._impl.setOutputHandler(outputhandler)

    def setErrorHandler(self, errorhandler):
        """
        Sets a new error handler.

        Args:
            errorhandler: The object handling AMPL errors and warnings.
        """
        self._errorhandler = errorhandler
        self._impl.setErrorHandler(errorhandler)

    def getOutputHandler(self):
        """
        Get the current output handler.

        Returns:
            The current output handler.
        """
        self._outputhandler = self._impl.getOutputHandler()
        return self._outputhandler

    def getErrorHandler(self):
        """
        Get the current error handler.

        Returns:
            The current error handler.
        """
        self._errorhandler = self._impl.getErrorHandler()
        return self._errorhandler

    def getVariables(self):
        """
        Get all the variables declared.
        """
        return MapEntities(Variable, self._impl.getVariables())

    def getConstraints(self):
        """
        Get all the constraints declared.
        """
        return MapEntities(Constraint, self._impl.getConstraints())

    def getObjectives(self):
        """
        Get all the objectives declared.
        """
        return MapEntities(Objective, self._impl.getObjectives())

    def getSets(self):
        """
        Get all the sets declared.
        """
        return MapEntities(Set.fromSetRef, self._impl.getSets())

    def getParameters(self):
        """
        Get all the parameters declared.
        """
        return MapEntities(
            Parameter.fromParameterRef, self._impl.getParameters()
        )
