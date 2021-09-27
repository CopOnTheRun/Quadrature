#!/usr/bin/env python3

"""
Module used to create and visulize Riemann sums.

Goals:
    * I'm learning about the factory method, and because there are different implementations with the same interface, it seems like this module could be a good way to practice the factory method pattern.
    * refresher+practice with matplotlib or whatever plotting library I choose to work with
    * replicate the picture on the wikipedia page for Riemann sums
    * upload said picture to wikipedia in svg format (current is jpg I think)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from itertools import zip_longest

import numpy as np
import matplotlib
from matplotlib import pyplot

from Interval import AnnotatedFunction, Interval, Method, Point

class Quadrature(ABC):
    """Abstract base class for methods of numerical integration which partition an interval into subintervals in order to calculate a definite intergral of a function."""

    def __init__(self, func: AnnotatedFunction, interval: Interval, method: Method) -> None:
        self.func = func
        self.interval = interval
        self.method = method

    @property
    def points(self) -> list[Point]:
        return [self.method.choose(self.func.func,p) for p in self.interval]

    @abstractmethod
    def calc(self) -> float:
        """The calculated output of the method used to approximate the function."""

    @abstractmethod
    def graph(self, ax: matplotlib.axes.Axes) -> None:
        """Takes a matplotlib axes and graphs the instance's shapes onto the axes"""

class Riemann(Quadrature):
    """A function on an interval. Take the sum using a certain method."""
    def calc(self) -> float:
        total: float = 0

        for partition, point, in zip(self.interval, self.points):
            total += partition.length * point.y

        return total

    def graph(self, ax: matplotlib.axes.Axes) -> matplotlib.axes.Axes:
        """Return and possibly write to a file, a graphic representation of the Riemann sum"""
        #plotting the points used for quadrature
        _, y_coor = zip(*self.points)

        #creating the bars
        starts = [x.start for x in self.interval]
        lengths = [x.length for x in self.interval]
        ax.bar(starts, y_coor, width=lengths, align="edge", edgecolor="black", linewidth=.5)

class Trapezoid(Quadrature):

    def __init__(self, func: AnnotatedFunction, interval: Interval):
        super().__init__(func, interval, Method.left())

    @property
    def points(self) -> list[Point]:
        """The same as super, but add an endpoint"""
        x = self.interval.end
        y = self.func.func(x)
        return super().points + [Point(x,y)]

    def calc(self) -> float:
        total: float = 0
        for partition in self.interval:
            h = partition.length
            a = self.func.func(partition.start)
            b = self.func.func(partition.end)
            total += (a+b)/2*h
        return total

    def graph(self, ax: matplotlib.axes.Axes) -> None:
        """Return and possibly write to a file, a graphic representation of the Riemann sum"""
        for point in self.points:
            ax.vlines(point.x,0,point.y,color="black",lw=.5)
        y_coor = [point.y for point in self.points]
        x_coor = [point.x for point in self.points]
        traps = ax.plot(x_coor, y_coor,lw=.5,color="black")
        ax.fill_between(np.linspace(self.interval.start,self.interval.end,len(y_coor)),y_coor)
        ax.hlines(0,self.interval.start,self.interval.end,lw=.5,color="black")

class Simpson(Quadrature):
    def __init__(self, func: AnnotatedFunction, interval: Interval) -> None:
        if len(interval.partitions) % 2 != 0:
            message = "Simson's rule only works with an even number of partitions."
            raise ValueError(message)
        #current implementation requires partitions to be of equal length, but because of floating points I've gotta aim for close enough to equal length
        if not all((interval[0].length - i.length < 10**-3 for i in interval)):
            message = "All partition lengths must be the same."
            raise ValueError(message)
        super().__init__(func, interval, Method.left())

    @property
    def points(self) -> list[Point]:
        """The same as super, but add an endpoint"""
        x = self.interval.end
        y = self.func.func(x)
        return super().points + [Point(x,y)]

    def parabolas(self) -> list[tuple[float,float,float]]:
        parabolas = []
        size = self.interval[0].length
        for p0,p1 in chunk_iter(self.interval,2):
            y0 = self.func.func(p0.start)
            y1 = self.func.func(p1.start)
            y2 = self.func.func(p1.end)
            A: float = (y0 - 2*y1 + y2)/(2*size**2)
            B: float = (y2 - y0)/(2*size)
            C: float = y1
            parabolas.append((A,B,C))
        return parabolas

    def calc(self) -> float:
        """Calculates the area using Simpson's rule. Note that unlike the other methods (trapezoid, Riemann), this method only works under the assumption that all partition sizes are the same. This is the reason that we can just multiply by the partition size/3 at the end and get area, instead of multiplying each subarea by the size of the partition.
        I expect I'll update this in the future to allow for differing partition sizes if it's not too difficult."""
        #not actual area until multiplied by partition_size/3
        area: float = self.points[0].y + self.points[-1].y
        for point in self.points[1:-1:2]:
            area += 4*point.y
        for point in self.points[2:-1:2]:
            area += 2*point.y
        return area*self.interval[0].length/3

    def graph(self, ax: matplotlib.axes.Axes) -> None:
        parabs = iter(self.parabolas())
        step_size = self.interval[0].length
        p = np.linspace(-step_size,step_size)
        colors = matplotlib.rcParams['axes.prop_cycle'].by_key()['color']
        for point in self.points:
            ax.vlines(point.x,0,point.y,color="black",lw=.5)

        for par0,par1 in chunk_iter(self.interval,2):
            x = np.linspace(par0.start,par1.end)
            A,B,C = next(parabs)
            y = A*p**2 + B*p + C
            ax.plot(x,y,lw=.5,color="black")
            ax.fill_between(x,y,color=colors[0])

        ax.hlines(0,self.interval.start,self.interval.end,lw=.5,color="black")

def chunk_iter(iters: Iterable[float], chunk_size: int):
    chunks = [iter(iters)] * chunk_size
    return zip_longest(*chunks,fillvalue=0)

def graph(quad: Quadrature, file_name: str = None) -> matplotlib.axes.Axes:
    """Return and possibly write to a file, a graphic representation of the Riemann sum"""
    #setting up matplotlib
    matplotlib.use("svg")
    pyplot.style.use("seaborn")
    matplotlib.rcParams['text.usetex'] = True

    #creating the figure
    fig = pyplot.figure()
    ax = fig.add_subplot(1,1,1)

    #this makes it so that the function curve goes past the bounds of the interval. Purely asthetics.
    overshoot = .025*abs(quad.interval.length)
    start = quad.interval.start - overshoot
    end = quad.interval.end + overshoot

    #creating function curve
    x = np.linspace(start, end, 200)
    y = quad.func.func(x)
    label = f"$y = {quad.func.string}$" if quad.func.string else "$y=f(x)$"
    ax.plot(x, y, color="black", label=label)
    ax.legend()

    #plotting the points used for quadrature
    x_coor, y_coor = zip(*quad.points)
    ax.plot(x_coor,y_coor,".",color="black")

    #creating the shapes
    quad.graph(ax)

    fig.tight_layout()

    if file_name:
        fig.savefig(file_name)

    return fig
